from io import BytesIO
from uuid import UUID
from zipfile import ZipFile
from PIL import Image

import geojson
from celery.result import AsyncResult
from celery.signals import worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray
import logging as log

from segment_anything import sam_model_registry, SamPredictor
from ultralytics import YOLO

from sketch_map_tool import celery_app as celery, get_config_value
from sketch_map_tool import map_generation
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.definitions import COLORS_MAPPING
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
from sketch_map_tool.upload_processing.create_marking_array import applyMLPipeline, create_marking_array
from sketch_map_tool.upload_processing.mapColors import mapColors
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
    map_img.write
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
    # zero shot segment anything model
    # creates masks based on image segmentation and bbox from object detection (YOLO)
    sam = sam_model_registry["vit_b"](init_model(get_config_value("neptune_model_id_sam")))

    mask_predictor = SamPredictor(sam)

    modelYOLO = YOLO(init_model(get_config_value("neptune_model_id_yolo")))

    def process(
        sketch_map_id: int, name: str, uuid: str, bbox: Bbox, mask_predictor, modelYOLO
    ) -> FeatureCollection:
        """Process a Sketch Map."""
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = to_array(r)
        r = clip(r, map_frames[uuid])
        img = Image.fromarray(r[:, :, ::-1]).convert("RGB") #RGB since Sam can only deal with RGB and not RGBA etc.
        masks, colors = applyMLPipeline(img,modelYOLO,mask_predictor)
        colors = [int(c)+1 for c in colors] # +1 because 0 is background

        r_ = create_marking_array(masks, colors, r)
        r_ = georeference(r_, bbox,True)
        r_ = polygonize(r_, name)
        r_ = geojson.load(r_)
        r_ = clean(r_)
        r_ = enrich(r_, {"name": name})
        r_ = mapColors(r_, COLORS_MAPPING)
        return r_

    return merge(
        [
            process(file_id, name, uuid, bbox, mask_predictor, modelYOLO)
            for file_id, name, uuid, bbox in zip(file_ids, file_names, uuids, bboxes)
        ]
    )
