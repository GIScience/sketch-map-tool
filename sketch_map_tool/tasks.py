import logging
from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

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
from sketch_map_tool.helpers import N_, to_array
from sketch_map_tool.models import Bbox, Layer, PaperFormat, Size
from sketch_map_tool.upload_processing import (
    clip,
    georeference,
    merge,
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
def init_worker(**kwargs):
    """Initializing database connection for worker"""
    db_client_celery.open_connection()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """Closing database connection for worker"""
    db_client_celery.close_connection()


@setup_logging.connect
def on_setup_logging(**kwargs):
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
    orientation: str,  # TODO: is not accessed
    size: Size,
    scale: float,
    layer: Layer,
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
    )
    db_client_celery.insert_map_frame(map_img, uuid, bbox, format_, orientation, layer)
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
@celery.task(bind=True)
def georeference_sketch_maps(
    self,
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    bboxes: dict[str, Bbox],
    layers: dict[str, Layer],
) -> AsyncResult | BytesIO:
    def process(
        sketch_map_id: int,
        uuid: str,
    ) -> BytesIO:
        """Process a Sketch Map and its attribution."""
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = to_array(r)
        r = clip(r, map_frames[uuid])
        r = georeference(r, bboxes[uuid])
        return r

    def get_attribution_file() -> BytesIO:
        attributions = []
        for layer in layers.values():
            attribution = get_attribution(layer)
            attribution = attribution.replace("<br />", "\n")
            attributions.append(attribution)
        return BytesIO("\n".join(attributions).encode())

    def zip_(file: BytesIO, file_name: str):
        with ZipFile(buffer, "a") as zip_file:
            name = ".".join(file_name.split(".")[:-1])
            zip_file.writestr(f"{name}.geotiff", file.read())

    buffer = BytesIO()
    for i, (file_id, uuid, file_name) in enumerate(zip(file_ids, uuids, file_names)):
        self.update_state(
            state="PROGRESS",
            meta={"current": i, "total": len(file_ids), "failures": []},
        )
        zip_(process(file_id, uuid), file_name)
    with ZipFile(buffer, "a") as zip_file:
        zip_file.writestr("attributions.txt", get_attribution_file().read())

    buffer.seek(0)
    return buffer


@celery.task(bind=True)
def digitize_sketches(
    self,
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    layers: dict[str, Layer],
    bboxes: dict[str, Bbox],
) -> AsyncResult | FeatureCollection:
    # Initialize ml-models. This has to happen inside of celery context.
    #
    # Zero shot segment anything model for automatic mask generation
    path = init_sam2()
    device = select_computation_device()
    sam2_model = build_sam2(
        config_file="sam2_hiera_b+.yaml",
        ckpt_path=path,
        device=device,
    )
    sam_predictor = SAM2ImagePredictor(sam2_model)

    # Custom trained model for object detection (obj) and classification (cls)
    # of markings and colors.
    if "osm" in layers.values():
        path = init_model(get_config_value("neptune_model_id_yolo_osm_obj"))
        yolo_obj_osm: YOLO_4 = YOLO_4(path)  # yolo object detection
        path = init_model(get_config_value("neptune_model_id_yolo_osm_cls"))
        yolo_cls_osm: YOLO = YOLO(path)  # yolo classification
    if "esri-world-imagery" in layers.values():
        path = init_model(get_config_value("neptune_model_id_yolo_esri_obj"))
        yolo_obj_esri: YOLO_4 = YOLO_4(path)
        path = init_model(get_config_value("neptune_model_id_yolo_esri_cls"))
        yolo_cls_esri: YOLO = YOLO(path)

    l = []  # noqa: E741
    failures = []
    for i, (file_id, file_name, uuid) in enumerate(zip(file_ids, file_names, uuids)):
        self.update_state(
            state="PROGRESS",
            meta={"current": i, "total": len(file_ids), "failures": failures},
        )
        # r = interim result
        r: BytesIO = db_client_celery.select_file(file_id)  # type: ignore
        r: NDArray = to_array(r)  # type: ignore
        r: NDArray = clip(r, map_frames[uuid])  # type: ignore
        if layers[uuid] == "osm":
            yolo_obj = yolo_obj_osm
            yolo_cls = yolo_cls_osm
        elif layers[uuid] == "esri-world-imagery":
            yolo_obj = yolo_obj_esri
            yolo_cls = yolo_cls_esri
        else:
            raise ValueError("Unexpected layer: " + layers[uuid])

        r: NDArray = detect_markings(
            r,
            map_frames[uuid],
            yolo_obj,
            yolo_cls,
            sam_predictor,
        )  # type: ignore
        if len(r) == 0:
            logging.warning("No markings were detected for file " + file_name)
            failures.append(file_name)
            continue
        # m = marking
        for m in r:
            m: BytesIO = georeference(m, bboxes[uuid], bgr=False)  # type: ignore
            m: FeatureCollection = polygonize(m, layer_name=file_name)  # type: ignore
            m: FeatureCollection = post_process(m, file_name)
            l.append(m)
    if len(l) == 0:
        raise MarkingDetectionError(N_("No markings have been detected."))
    return merge(l)


@celery.task
def cleanup_map_frames():
    """Cleanup map frames stored in the database."""
    db_client_celery.cleanup_map_frames()
    return True


@celery.task
def cleanup_blobs(*_, map_frame_uuids: list):
    """Cleanup uploaded files stored in the database.

    Arguments are ignored. They are only part of the signature because of the usage in
    a celery chain.
    """
    db_client_celery.cleanup_blob(map_frame_uuids)
    return True
