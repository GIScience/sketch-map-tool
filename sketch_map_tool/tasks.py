from io import BytesIO

import cv2
import numpy as np
from celery import chain, group
from celery.result import AsyncResult
from numpy.typing import NDArray

from sketch_map_tool import celery_app as celery
from sketch_map_tool import map_generation, upload_processing
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
# fmt: off
def generate_digitized_results(files) -> AsyncResult:
    args = upload_processing.read_qr_code(t_buffer_to_array(files[0]))
    uuid = args["uuid"]
    bbox = args["bbox"]

    map_frame_buffer = celery.AsyncResult(uuid).get()[1]
    map_frame = t_buffer_to_array(map_frame_buffer)

    # Design Celery Workflow
    #
    # https://docs.celeryq.dev/en/stable/userguide/canvas.html
    #
    # t_    -> task
    # c_    -> chain of tasks (sequential)
    # group -> group of tasks (parallel)
    #
    def c_digitize(color: str) -> chain:
        """Digitize one color of a Sketch Map."""
        return (
                t_detect.s(map_frame, color)
                | t_georeference.s(bbox)
                | t_polygonize.s(color)
                )

    def c_process(sketch_map: BytesIO) -> chain:
        """Process a Sketch Map."""
        return (
            t_buffer_to_array.s(sketch_map)
            | t_clip.s(map_frame)
            | group([c_digitize(c) for c in COLORS])
            | t_merge.s()
        )

    def c_workflow(files) -> chain:
        """Start processing workflow for each file."""
        return (
                group([c_process(f) for f in files])
                | t_zip.s()
                )
    return c_workflow(files)
    # fmt: on


@celery.task()
def t_buffer_to_array(buffer: BytesIO) -> AsyncResult | NDArray:
    buffer.seek(0)
    return cv2.imdecode(
        np.fromstring(buffer.read(), dtype="uint8"), cv2.IMREAD_UNCHANGED
    )


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
def t_merge(geojsons: list) -> AsyncResult | BytesIO:
    return upload_processing.merge(geojsons)


@celery.task()
def t_zip(args) -> AsyncResult | BytesIO:
    return args[0]
