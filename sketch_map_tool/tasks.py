from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import cv2
import geojson
import numpy as np
from celery import chain, group
from celery.result import AsyncResult
from celery.signals import worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray

from sketch_map_tool import celery_app as celery
from sketch_map_tool import map_generation, upload_processing
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.definitions import COLORS
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.upload_processing.detect_markings import prepare_img_for_markings
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
        uuid,
        bbox,
        format_,
        orientation,
        size,
        scale,
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


# Celery Workflow
#
# https://docs.celeryq.dev/en/stable/userguide/canvas.html
#
# t_    -> task
# c_    -> chain of tasks (sequential)
# group -> group of tasks (parallel)
# chord -> group chained to a task
#
# fmt: off


# 2. DIGITIZE RESULTS
#
def georeference_sketch_maps(file_ids: list[int], map_frame: NDArray, bbox: Bbox) -> str:

    def c_process(sketch_map_id: int, map_frame: BytesIO, bbox: Bbox) -> chain:
        """Process a Sketch Map."""
        return (
            t_preprocess.s(sketch_map_id, map_frame)
            | t_georeference.s(bbox)
        )

    def c_workflow(file_ids: list[int]) -> chain:
        """Start processing workflow for each file."""
        return (
                group([c_process.s(i, map_frame, bbox) for i in file_ids])
                | t_zip.s()  # chord
                )

    return c_workflow(file_ids).apply_async().id


def digitize_sketches(file_ids: list[int], map_frame: NDArray, bbox: Bbox) -> str:

    def c_process(sketch_map_id: int, name: str) -> chain:
        """Process a Sketch Map."""
        return (
            t_preprocess.s(sketch_map_id, map_frame)
            | t_prepare_digitize.s(map_frame)
            | group([t_digitize.s(bbox, color, name) for color in COLORS])
            | t_merge.s()  # chord
        )

    def c_workflow(file_ids: list[int], file_names: list[str]) -> chain:
        """Start processing workflow for each file."""
        return (
                group([c_process(i, n) for i, n in zip(file_ids, file_names)])
                | t_merge.s()  # chord
                )
    file_names = [db_client_flask.select_file_name(i) for i in file_ids]
    return c_workflow(file_ids, file_names).apply_async().id


# Celery Tasks
#
# t_ -> task
#
# fmt: on


@celery.task()
def t_preprocess(sketch_map_id: int, map_frame: NDArray) -> AsyncResult | NDArray:
    r = t_read_file(sketch_map_id)
    r = t_to_array(r)
    r = t_clip(r, map_frame)
    return r


@celery.task()
def t_prepare_digitize(
    sketch_map_frame: NDArray,
    map_frame: NDArray,
) -> AsyncResult | NDArray:
    return prepare_img_for_markings(map_frame, sketch_map_frame)


@celery.task()
def t_digitize(
    sketch_map_frame: NDArray,
    bbox: Bbox,
    color: str,
    name: str,
) -> AsyncResult | FeatureCollection:
    """Digitize one color of a Sketch Map."""
    r = t_detect(sketch_map_frame, color)
    r = t_georeference(r, bbox)
    r = t_polygonize(r, color)
    r = t_to_geojson(r)
    r = t_clean(r)
    r = t_enrich(r, {"color": color, "name": name})
    return r


@celery.task()
def t_read_file(id_: int) -> bytes:
    return db_client_celery.select_file(id_)


@celery.task()
def t_to_array(buffer: bytes) -> AsyncResult | NDArray:
    return cv2.imdecode(np.fromstring(buffer, dtype="uint8"), cv2.IMREAD_UNCHANGED)


@celery.task()
def t_clip(sketch_map: NDArray, map_frame: NDArray) -> AsyncResult | NDArray:
    return upload_processing.clip(sketch_map, map_frame)


@celery.task()
def t_detect(sketch_map_frame: NDArray, color) -> AsyncResult | NDArray:
    return upload_processing.detect_markings(sketch_map_frame, color)


@celery.task()
def t_georeference(sketch_map_frame: NDArray, bbox: Bbox) -> AsyncResult | BytesIO:
    return upload_processing.georeference(sketch_map_frame, bbox)


@celery.task()
def t_polygonize(geotiff: BytesIO, layer_name: str) -> AsyncResult | BytesIO:
    return upload_processing.polygonize(geotiff, layer_name)


@celery.task()
def t_to_geojson(buffer: BytesIO) -> AsyncResult | FeatureCollection:
    return geojson.load(buffer)


@celery.task()
def t_clean(fc: FeatureCollection) -> AsyncResult | FeatureCollection:
    return upload_processing.clean(fc)


@celery.task()
def t_enrich(
    fc: FeatureCollection, properties: dict
) -> AsyncResult | FeatureCollection:
    return upload_processing.enrich(fc, properties)


@celery.task()
def t_merge(fcs: list[FeatureCollection]) -> AsyncResult | FeatureCollection:
    return upload_processing.merge(fcs)


@celery.task()
def t_zip(files: list) -> AsyncResult | BytesIO:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for i, file in enumerate(files):
            zip_file.writestr(str(i) + ".geotiff", file.read())
    buffer.seek(0)
    return buffer


@celery.task()
def t_geopackage(feature_collections: list) -> AsyncResult | BytesIO:
    return upload_processing.geopackage(feature_collections)
