import logging
from io import BytesIO

from celery.result import AsyncResult
from celery.signals import setup_logging, worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from ultralytics import YOLO
from ultralytics_MB import YOLO as YOLO_MB

from sketch_map_tool import CONFIG, map_generation
from sketch_map_tool import celery_app as celery
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.definitions import get_attribution
from sketch_map_tool.exceptions import MarkingDetectionError
from sketch_map_tool.helpers import N_, merge, to_array
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.openaerialmap import client as oam_client
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
    global yolo_obj_esri
    global yolo_cls

    path = init_sam2()
    device = select_computation_device()
    sam2_model = build_sam2(
        config_file="sam2_hiera_b+.yaml",
        ckpt_path=path,
        device=device,
    )
    sam_predictor = SAM2ImagePredictor(sam2_model)

    yolo_obj_osm = YOLO_MB(init_model(CONFIG.yolo_osm_obj))
    yolo_obj_esri = YOLO_MB(init_model(CONFIG.yolo_esri_obj))
    yolo_cls = YOLO(init_model(CONFIG.yolo_cls))


@worker_process_shutdown.connect
def shutdown_worker(**_):
    """Closing database connection for worker"""
    logging.debug("Closing database connection.")
    db_client_celery.close_connection()


@setup_logging.connect
def on_setup_logging(**_):
    level = getattr(logging, CONFIG.log_level.upper())
    format = "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s"
    logging.basicConfig(
        level=level,
        format=format,
    )


# 1. GENERATE SKETCH MAP & QUALITY REPORT
#
@celery.task(bind=True)
def generate_sketch_map(
    self,
    bbox: Bbox,
    bbox_wgs84: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    scale: float,
    layer: str,
    ip: str | None = None,
    user_agent: str | None = None,
    geo_ip_city: str | None = None,
    geo_ip_country: str | None = None,
    geo_ip_country_iso_code: str | None = None,
    geo_ip_centroid_wgs84: str | None = None,
) -> BytesIO | AsyncResult:
    """Generate and returns a sketch map as PDF and stores the map frame in DB."""
    if layer.startswith("oam"):
        map_image = oam_client.get_map_image(bbox_wgs84, size, layer)
    else:
        map_image = wms_client.get_map_image(bbox, size, layer)
    qr_code_ = map_generation.qr_code(
        self.request.id,
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
    )
    db_client_celery.insert_map_frame(
        map_img,
        self.request.id,
        bbox,
        bbox_wgs84,
        format_,
        orientation,
        layer,
        ip,
        user_agent,
        geo_ip_city,
        geo_ip_country,
        geo_ip_country_iso_code,
        geo_ip_centroid_wgs84,
    )
    return map_pdf


# 2. DIGITIZE RESULTS
#
def digitize_sketches(
    file_id: int,
    file_name: str,
    map_frame: NDArray,
    sketch_map_frame: NDArray,
    layer: str,
    bbox: Bbox,
) -> FeatureCollection:
    if layer == "osm":
        yolo_obj = yolo_obj_osm
    elif layer.startswith(("esri-world-imagery", "oam")):
        yolo_obj = yolo_obj_esri
    else:
        raise ValueError("Unexpected layer: " + layer)

    markings: list[NDArray] = detect_markings(
        sketch_map_frame,
        map_frame,
        yolo_obj,
        yolo_cls,
        sam_predictor,
    )
    # m = marking
    l = []  # noqa: E741
    for m in markings:
        m: BytesIO = georeference(m, bbox, bgr=False)  # type: ignore
        m: FeatureCollection = polygonize(m, layer_name=file_name)  # type: ignore
        m: FeatureCollection = post_process(m, file_name, bbox)
        l.append(m)
    if len(l) == 0:
        raise MarkingDetectionError(
            N_(f"For '{file_name}' (ID: {file_id}) no markings have been detected.")
        )
    return merge(l)


@celery.task
def upload_processing(
    file_id: int,
    file_name: str,
    map_frame: NDArray,
    layer: str,
    bbox: Bbox,
) -> (
    AsyncResult
    | tuple[
        str,
        str,
        BytesIO,
        FeatureCollection,
        list,
    ]
):
    """Georeference and digitize given sketch map."""
    errors = []
    sketch_map_uploaded = db_client_celery.select_file(file_id)
    sketch_map_frame = clip(to_array(sketch_map_uploaded), map_frame)
    sketch_map_frame_georeferenced = georeference(sketch_map_frame, bbox)
    try:
        sketches = digitize_sketches(
            file_id,
            file_name,
            map_frame,
            sketch_map_frame,
            layer,
            bbox,
        )
    except MarkingDetectionError as error:
        sketches = FeatureCollection(features=[])
        errors.append(error)

    attribution = get_attribution(layer)
    return (
        file_name,
        attribution,
        sketch_map_frame_georeferenced,
        sketches,
        errors,
    )


@celery.task(ignore_result=True)
def cleanup_map_frames():
    """Cleanup map frames stored in the database."""
    db_client_celery.cleanup_map_frames()


@celery.task(ignore_result=True)
def cleanup_blobs(file_ids: list[int]):
    """Cleanup uploaded files stored in the database."""
    db_client_celery.cleanup_blob(file_ids)
