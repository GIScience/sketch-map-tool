import logging
from io import BytesIO
from uuid import UUID

import celery.states
from celery.result import AsyncResult
from celery.signals import setup_logging, worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from ultralytics import YOLO
from ultralytics_4bands import YOLO as YOLO_4

from sketch_map_tool import celery_app as celery
from sketch_map_tool import get_config_value, map_generation
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.definitions import get_attribution
from sketch_map_tool.exceptions import MarkingDetectionError
from sketch_map_tool.helpers import N_, merge, to_array
from sketch_map_tool.models import Bbox, Layer, PaperFormat, Size
from sketch_map_tool.upload_processing import (
    clip,
    georeference,
    polygonize,
    post_process,
)
from sketch_map_tool.upload_processing.detect_markings import detect_markings
from sketch_map_tool.upload_processing.ml_models import (
    init_model,
    init_sam2,
    select_computation_device,
)
from sketch_map_tool.wms import client as wms_client


@worker_process_init.connect
def init_worker_db_connection(**_):
    """Initializing database connection for worker."""
    logging.debug("Initialize database connection.")
    db_client_celery.open_connection()


@worker_process_init.connect
def init_worker_ml_models(**_):
    """Initializing machine-learning models for worker.

    Custom trained model for object detection (obj) and classification (cls) of
    markings and colors.

    Zero shot segment anything model (sam) for automatic mask generation.
    """
    logging.info("Initialize ml-models.")
    global sam_predictor
    global yolo_obj_osm
    global yolo_cls_osm
    global yolo_obj_esri
    global yolo_cls_esri

    path = init_sam2()
    device = select_computation_device()
    sam2_model = build_sam2(
        config_file="sam2_hiera_b+.yaml",
        ckpt_path=path,
        device=device,
    )
    sam_predictor = SAM2ImagePredictor(sam2_model)

    yolo_obj_osm = YOLO_4(init_model(get_config_value("neptune_model_id_yolo_osm_obj")))
    yolo_cls_osm = YOLO(init_model(get_config_value("neptune_model_id_yolo_osm_cls")))
    yolo_obj_esri = YOLO_4(
        init_model(get_config_value("neptune_model_id_yolo_esri_obj"))
    )
    yolo_cls_esri = YOLO(init_model(get_config_value("neptune_model_id_yolo_esri_cls")))


@worker_process_shutdown.connect
def shutdown_worker(**_):
    """Closing database connection for worker"""
    logging.debug("Closing database connection.")
    db_client_celery.close_connection()


@setup_logging.connect
def on_setup_logging(**_):
    level = getattr(logging, get_config_value("log-level").upper())
    format = "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s"
    logging.basicConfig(
        level=level,
        format=format,
    )


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
    layer: Layer,
    aruco: bool,
) -> BytesIO | AsyncResult:
    """Generate and returns a sketch map as PDF and stores the map frame in DB."""
    map_image = wms_client.get_map_image(bbox, size, layer)
    qr_code_ = map_generation.qr_code(
        str(uuid),
        bbox,
        layer,
        format_,
    )
    map_pdf, map_img = map_generation.generate_pdf(
        map_image,
        qr_code_,
        format_,
        scale,
        layer,
        aruco,
    )
    db_client_celery.insert_map_frame(
        map_img,
        uuid,
        bbox,
        format_,
        orientation,
        layer,
        aruco,
    )
    return map_pdf


@celery.task()
def generate_quality_report(bbox: Bbox) -> BytesIO | AsyncResult:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    # report = get_report(bbox)
    # return generate_report_pdf(report)
    return BytesIO(b"")


# 2. DIGITIZE RESULTS
#
@celery.task()
def georeference_sketch_map(
    file_id: int,
    file_name: str,
    map_frame: NDArray,
    layer: Layer,
    bbox: Bbox,
) -> AsyncResult | tuple[str, str, BytesIO]:
    """Georeference uploaded Sketch Map.

    Returns file name, attribution text and to the map extend clipped and georeferenced
    sketch map as GeoTiff.
    """
    # r = interim result
    r = db_client_celery.select_file(file_id)
    r = to_array(r)
    r = clip(r, map_frame)
    r = georeference(r, bbox)
    return file_name, get_attribution(layer), r


@celery.task
def digitize_sketches(
    file_id: int,
    file_name: str,
    map_frame: NDArray,
    layer: Layer,
    bbox: Bbox,
) -> AsyncResult | FeatureCollection:
    # r = interim result
    r: BytesIO = db_client_celery.select_file(file_id)  # type: ignore
    r: NDArray = to_array(r)  # type: ignore
    r: NDArray = clip(r, map_frame)  # type: ignore
    if layer == "osm":
        yolo_obj = yolo_obj_osm
        yolo_cls = yolo_cls_osm
    elif layer == "esri-world-imagery":
        yolo_obj = yolo_obj_esri
        yolo_cls = yolo_cls_esri
    else:
        raise ValueError("Unexpected layer: " + layer)

    r: NDArray = detect_markings(
        r,
        map_frame,
        yolo_obj,
        yolo_cls,
        sam_predictor,
    )  # type: ignore
    # m = marking
    l = []  # noqa: E741
    for m in r:
        m: BytesIO = georeference(m, bbox, bgr=False)  # type: ignore
        m: FeatureCollection = polygonize(m, layer_name=file_name)  # type: ignore
        m: FeatureCollection = post_process(m, file_name)
        l.append(m)
    if len(l) == 0:
        raise MarkingDetectionError(
            N_(f"For '{file_name}' (ID: {file_id}) no markings have been detected.")
        )
    return merge(l)


@celery.task(ignore_result=True)
def cleanup_map_frames():
    """Cleanup map frames stored in the database."""
    db_client_celery.cleanup_map_frames()


@celery.task(ignore_result=True)
def cleanup_blobs(file_ids: list[int]):
    """Cleanup uploaded files stored in the database."""
    db_client_celery.cleanup_blob(file_ids)
