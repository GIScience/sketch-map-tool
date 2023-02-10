from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import cv2
import geojson
import numpy as np
from celery.result import AsyncResult
from celery.signals import worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray

from sketch_map_tool import celery_app as celery
from sketch_map_tool import map_generation, upload_processing
from sketch_map_tool.database import client_celery as db_client_celery
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
def t_generate_sketch_map(
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
def t_generate_quality_report(bbox: Bbox) -> BytesIO | AsyncResult:
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
# st_   -> subtask (not a real celery task)
# c_    -> chain of tasks (sequential)
# group -> group of tasks (parallel)
# chord -> group chained to a task
#
# fmt: off


# 2. DIGITIZE RESULTS
#


@celery.task()
def t_georeference_sketch_maps(file_ids: list[int], map_frame: NDArray, bbox: Bbox) -> AsyncResult | BytesIO:
    def st_process(sketch_map_id: int) -> AsyncResult | BytesIO:
        """Process a Sketch Map."""
        r = st_read_file(sketch_map_id)
        r = st_to_array(r)
        r = st_clip(r, map_frame)
        r = st_georeference(r, bbox)
        return r

    def st_workflow() -> AsyncResult | BytesIO:
        """Start processing workflow for each file."""
        r = [st_process(i) for i in file_ids]
        r = st_zip(r)  # chord
        return r

    return st_workflow()


@celery.task()
def t_digitize_sketches(file_ids: list[int], file_names: list[str], map_frame: NDArray, bbox: Bbox) -> AsyncResult | FeatureCollection:
    def st_process(sketch_map_id: int, name: str) -> AsyncResult | FeatureCollection:
        """Process a Sketch Map."""
        r = st_read_file(sketch_map_id)
        r = st_to_array(r)
        r = st_clip(r, map_frame)
        r = st_prepare_digitize(r, map_frame)
        rlist = []
        for color in COLORS:
            r1 = st_detect(r, color)
            r1 = st_georeference(r1, bbox)
            r1 = st_polygonize(r1, color)
            r1 = st_to_geojson(r1)
            r1 = st_clean(r1)
            r1 = st_enrich(r1, {"color": color, "name": name})
            rlist.append(r1)
        r = st_merge(rlist)
        return r

    def st_workflow(file_ids: list[int], file_names: list[str]) -> AsyncResult | FeatureCollection:
        """Start processing workflow for each file."""
        r = [st_process(i, n) for i, n in zip(file_ids, file_names)]
        r = st_merge(r)  # chord
        return r

    return st_workflow(file_ids, file_names)


# Celery Tasks
#
# t_ -> task
#
# fmt: on


def st_prepare_digitize(
    sketch_map_frame: NDArray,
    map_frame: NDArray,
) -> AsyncResult | NDArray:
    return prepare_img_for_markings(map_frame, sketch_map_frame)


def st_read_file(id_: int) -> bytes:
    return db_client_celery.select_file(id_)


def st_to_array(buffer: bytes) -> AsyncResult | NDArray:
    return cv2.imdecode(np.fromstring(buffer, dtype="uint8"), cv2.IMREAD_UNCHANGED)


def st_clip(sketch_map: NDArray, map_frame: NDArray) -> AsyncResult | NDArray:
    return upload_processing.clip(sketch_map, map_frame)


def st_detect(sketch_map_frame: NDArray, color) -> AsyncResult | NDArray:
    return upload_processing.detect_markings(sketch_map_frame, color)


def st_georeference(sketch_map_frame: NDArray, bbox: Bbox) -> AsyncResult | BytesIO:
    return upload_processing.georeference(sketch_map_frame, bbox)


def st_polygonize(geotiff: BytesIO, layer_name: str) -> AsyncResult | BytesIO:
    return upload_processing.polygonize(geotiff, layer_name)


def st_to_geojson(buffer: BytesIO) -> AsyncResult | FeatureCollection:
    return geojson.load(buffer)


def st_clean(fc: FeatureCollection) -> AsyncResult | FeatureCollection:
    return upload_processing.clean(fc)


def st_enrich(
    fc: FeatureCollection, properties: dict
) -> AsyncResult | FeatureCollection:
    return upload_processing.enrich(fc, properties)


def st_merge(fcs: list[FeatureCollection]) -> AsyncResult | FeatureCollection:
    return upload_processing.merge(fcs)


def st_zip(files: list) -> AsyncResult | BytesIO:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for i, file in enumerate(files):
            zip_file.writestr(str(i) + ".geotiff", file.read())
    buffer.seek(0)
    return buffer


def st_geopackage(feature_collections: list) -> AsyncResult | BytesIO:
    return upload_processing.geopackage(feature_collections)
