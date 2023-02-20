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
from sketch_map_tool import map_generation
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.definitions import COLORS
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.upload_processing import (
    clean,
    clip,
    detect_markings,
    enrich,
    georeference,
    merge,
    polygonize,
    prepare_img_for_markings,
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


# 2. DIGITIZE RESULTS
#
@celery.task()
def georeference_sketch_maps(
    file_ids: list[int],
    map_frame: NDArray,
    bbox: Bbox,
) -> AsyncResult | BytesIO:
    def process(sketch_map_id: int) -> BytesIO:
        """Process a Sketch Map."""
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = st_to_array(r)
        r = clip(r, map_frame)
        r = georeference(r, bbox)
        return r

    def zip_(files: list) -> BytesIO:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zip_file:
            for i, file in enumerate(files):
                zip_file.writestr(str(i) + ".geotiff", file.read())
        buffer.seek(0)
        return buffer

    return zip_([process(i) for i in file_ids])


@celery.task()
def digitize_sketches(
    file_ids: list[int],
    file_names: list[str],
    map_frame: NDArray,
    bbox: Bbox,
) -> AsyncResult | FeatureCollection:
    def process(sketch_map_id: int, name: str) -> FeatureCollection:
        """Process a Sketch Map."""
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = st_to_array(r)
        r = clip(r, map_frame)
        r = prepare_img_for_markings(map_frame, r)
        geojsons = []
        for color in COLORS:
            r_ = detect_markings(r, color)
            r_ = georeference(r_, bbox)
            r_ = polygonize(r_, color)
            r_ = geojson.load(r_)
            r_ = clean(r_)
            r_ = enrich(r_, {"color": color, "name": name})
            geojsons.append(r_)
        return merge(geojsons)

    return merge(
        [process(file_id, name) for file_id, name in zip(file_ids, file_names)]
    )


def st_to_array(buffer: bytes) -> NDArray:
    return cv2.imdecode(np.fromstring(buffer, dtype="uint8"), cv2.IMREAD_UNCHANGED)
