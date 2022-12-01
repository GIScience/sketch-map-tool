import json
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

import cv2
import geojson
import numpy as np
from celery import chain, group
from celery.result import AsyncResult
from geojson import GeoJSON
from numpy.typing import NDArray

from sketch_map_tool import celery_app as celery
from sketch_map_tool import map_generation, upload_processing
from sketch_map_tool.data_store import client as ds_client
from sketch_map_tool.definitions import COLORS
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.wms import client as wms_client


@celery.task(bind=True)
def generate_sketch_map(
    self,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    scale: float,
) -> BytesIO | AsyncResult:
    """Generate a sketch map as PDF."""
    raw = wms_client.get_map_image(bbox, size)
    map_image = wms_client.as_image(raw)
    qr_code_ = map_generation.qr_code(
        self.request.id,
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
    return map_pdf, map_img


@celery.task()
def generate_quality_report(bbox: Bbox) -> BytesIO | AsyncResult:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    report = get_report(bbox)
    return generate_report_pdf(report)


# GENERATE DIGITIZED RESULTS
#
def generate_digitized_results(files) -> str:
    args = upload_processing.read_qr_code(t_to_array(files[0]))
    uuid = args["uuid"]
    bbox = args["bbox"]

    map_frame_buffer = celery.AsyncResult(uuid).get()[1]
    map_frame = t_to_array(map_frame_buffer)

    result_id_1 = georeference_sketch_maps(files, map_frame, bbox)
    result_id_2 = digitize_sketches(files, map_frame, bbox)

    # Unique id for current request
    uuid = str(uuid4())
    # Mapping of request id to multiple tasks id's
    request_task = {
        uuid: json.dumps(
            {
                "raster-results": str(result_id_1),
                "vector-results": str(result_id_2),
            }
        )
    }
    ds_client.set(request_task)
    return uuid


# Design Celery Workflow
#
# https://docs.celeryq.dev/en/stable/userguide/canvas.html
#
# t_    -> task
# c_    -> chain of tasks (sequential)
# group -> group of tasks (parallel)
#
# fmt: off
def georeference_sketch_maps(files, map_frame, bbox) -> str:

    def c_process(sketch_map: BytesIO) -> chain:
        """Process a Sketch Map."""
        return (t_to_array.s(sketch_map) | t_clip.s(map_frame) | t_georeference.s(bbox))

    def c_workflow(files) -> chain:
        """Start processing workflow for each file."""
        return (group([c_process(f) for f in files]) | t_zip.s())

    return c_workflow(files).apply_async().id


def digitize_sketches(files, map_frame, bbox) -> str:

    def c_digitize(color: str) -> chain:
        """Digitize one color of a Sketch Map."""
        # TODO: Avoid redundant code execution.
        # If detect markings is executed for the same image but different colors,
        # steps like contrast enhancements are executed multiple times.
        return (
                t_detect.s(map_frame, color)
                | t_georeference.s(bbox)
                | t_polygonize.s(color)
                | t_to_geojson.s()
                | t_clean.s()
                )

    def c_process(sketch_map: BytesIO) -> chain:
        """Process a Sketch Map."""
        return (
            t_to_array.s(sketch_map)
            | t_clip.s(map_frame)
            | group([c_digitize(c) for c in COLORS])
            | t_merge.s()
        )

    def c_workflow(files) -> chain:
        """Start processing workflow for each file."""
        return (
                group([c_process(f) for f in files])
                | t_merge.s()
                )

    return c_workflow(files).apply_async().id
    # fmt: on


@celery.task()
def t_to_array(buffer: BytesIO) -> AsyncResult | NDArray:
    buffer.seek(0)
    return cv2.imdecode(
        np.fromstring(buffer.read(), dtype="uint8"), cv2.IMREAD_UNCHANGED
    )


@celery.task()
def t_to_geojson(buffer: BytesIO) -> AsyncResult | GeoJSON:
    return geojson.load(buffer)


def t_to_buffer(geojson_object: GeoJSON) -> AsyncResult | BytesIO:
    return BytesIO(geojson.dumps(geojson_object).encode("utf-8"))


@celery.task()
def t_clip(sketch_map: NDArray, map_frame: NDArray) -> AsyncResult | NDArray:
    return upload_processing.clip(sketch_map, map_frame)


@celery.task()
def t_detect(
    sketch_map_frame: NDArray, map_frame: NDArray, color
) -> AsyncResult | NDArray:
    return upload_processing.detect_markings(map_frame, sketch_map_frame, color)


@celery.task()
def t_georeference(sketch_map_frame: NDArray, bbox: Bbox) -> AsyncResult | BytesIO:
    return upload_processing.georeference(sketch_map_frame, bbox)


@celery.task()
def t_polygonize(geotiff: BytesIO, layer_name: str) -> AsyncResult | BytesIO:
    return upload_processing.polygonize(geotiff, layer_name)


@celery.task()
def t_clean(geojson: BytesIO) -> AsyncResult | BytesIO:
    return upload_processing.clean(geojson)


@celery.task()
def t_merge(feature_collections: list) -> AsyncResult | BytesIO:
    return upload_processing.merge(feature_collections)


@celery.task()
def t_zip(files: list) -> AsyncResult | BytesIO:
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as zip_file:
        for i, file in enumerate(files):
            zip_file.writestr(str(i) + ".geotiff", file.read())
    buffer.seek(0)
    return buffer


@celery.task()
def t_geopackage(feature_collections: list) -> AsyncResult | BytesIO:
    return upload_processing.geopackage(feature_collections)
