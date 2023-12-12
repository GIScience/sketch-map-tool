from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import geojson
from celery.result import AsyncResult
from celery.signals import worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray
from segment_anything import SamPredictor, sam_model_registry
from ultralytics import YOLO

from sketch_map_tool import celery_app as celery
from sketch_map_tool import get_config_value, map_generation
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.helpers import to_array
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.upload_processing import (
    clean,
    clip,
    enrich,
    georeference,
    merge,
    polygonize,
)
from sketch_map_tool.upload_processing.detect_markings import detect_markings
from sketch_map_tool.upload_processing.ml_models import init_model
from sketch_map_tool.wms import client as wms_client


@worker_process_init.connect
def init_worker(**kwargs):
    """Initializing database connection for worker"""
    db_client_celery.open_connection()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """Closing database connection for worker"""
    db_client_celery.close_connection()


# 1. GENERATE SKETCH MAP & QUALITY REPORT
#
@celery.task()
def generate_sketch_map(
    uuid: UUID,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    scale: float,
) -> BytesIO | AsyncResult:
    """Generate and returns a sketch map as PDF and stores the map frame in DB."""
    raw = wms_client.get_map_image(bbox, size)
    map_image = wms_client.as_image(raw)
    qr_code_ = map_generation.qr_code(
        str(uuid),
        bbox,
        format_,
    )
    map_pdf, map_img = map_generation.generate_pdf(
        map_image,
        qr_code_,
        format_,
        scale,
    )
    db_client_celery.insert_map_frame(map_img, uuid)
    return map_pdf


@celery.task()
def generate_quality_report(bbox: Bbox) -> BytesIO | AsyncResult:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    report = get_report(bbox)
    return generate_report_pdf(report)


# 2. DIGITIZE RESULTS
#
@celery.task()
def georeference_sketch_maps(
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    bboxes: list[Bbox],
) -> AsyncResult | BytesIO:
    def process(sketch_map_id: int, uuid: str, bbox: Bbox) -> BytesIO:
        """Process a Sketch Map.

        :param sketch_map_id: ID under which uploaded file is stored in the database.
        :param uuid: UUID under which the sketch map was created.
        :bbox: Bounding box of the AOI on the sketch map.
        :return: Georeferenced image (GeoTIFF) of the sketch map .
        """
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = to_array(r)
        r = clip(r, map_frames[uuid])
        r = georeference(r, bbox)
        return r

    def zip_(file: BytesIO, file_name: str):
        with ZipFile(buffer, "a") as zip_file:
            name = ".".join(file_name.split(".")[:-1])
            zip_file.writestr(f"{name}.geotiff", file.read())

    buffer = BytesIO()
    for file_id, uuid, bbox, file_name in zip(file_ids, uuids, bboxes, file_names):
        zip_(process(file_id, uuid, bbox), file_name)
    buffer.seek(0)
    return buffer


@celery.task()
def digitize_sketches(
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    bboxes: list[Bbox],
) -> AsyncResult | FeatureCollection:
    # Initialize ml-models. This has to happen inside of celery context.
    # Custom trained model for object detection of markings and colors
    yolo_path = init_model(get_config_value("neptune_model_id_yolo"))
    yolo_model = YOLO(yolo_path)
    # Zero shot segment anything model
    sam_path = init_model(get_config_value("neptune_model_id_sam"))
    sam_model = sam_model_registry["vit_b"](sam_path)
    sam_predictor = SamPredictor(sam_model)  # mask predictor

    def process(
        sketch_map_id: int,
        name: str,
        uuid: str,
        bbox: Bbox,
        sam_predictor: SamPredictor,
        yolo_model: YOLO,
    ) -> FeatureCollection:
        """Process a Sketch Map."""
        # r = interim result
        r: BytesIO = db_client_celery.select_file(sketch_map_id)  # type: ignore
        r: NDArray = to_array(r)  # type: ignore
        r: NDArray = clip(r, map_frames[uuid])  # type: ignore
        r: NDArray = detect_markings(r, yolo_model, sam_predictor)  # type: ignore
        r: BytesIO = georeference(r, bbox, bgr=False)  # type: ignore
        r: BytesIO = polygonize(r, name)  # type: ignore
        r: FeatureCollection = geojson.load(r)  # type: ignore
        r: FeatureCollection = clean(r)  # type: ignore
        r: FeatureCollection = enrich(r, {"name": name})  # type: ignore
        return r

    return merge(
        [
            process(file_id, name, uuid, bbox, sam_predictor, yolo_model)
            for file_id, name, uuid, bbox in zip(file_ids, file_names, uuids, bboxes)
        ]
    )
