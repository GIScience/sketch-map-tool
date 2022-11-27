from io import BytesIO

import cv2
import numpy as np
from celery import group
from celery.result import AsyncResult
from numpy.typing import NDArray

from sketch_map_tool import celery_app as celery
from sketch_map_tool import map_generation, upload_processing
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
def generate_digitized_results(files):
    args = upload_processing.qr_code_reader(buffer_to_array(files[0]))
    uuid = args["uuid"]
    # bbox = args["bbox"]

    map_frame_buffer = celery.AsyncResult(uuid).get()[1]
    map_frame = buffer_to_array(map_frame_buffer)

    workflow = (
        group(
            [
                (
                    buffer_to_array.s(sketch_map)
                    | clip.s(map_frame)
                    | detect.s(map_frame)
                )
                for sketch_map in files
            ]
        )
        | aggregate.s()
    )
    result = workflow.apply_async()
    return result.id


@celery.task()
def buffer_to_array(buffer: BytesIO) -> NDArray:
    buffer.seek(0)
    return cv2.imdecode(
        np.fromstring(buffer.read(), dtype="uint8"), cv2.IMREAD_UNCHANGED
    )


@celery.task()
def clip(sketch_map: NDArray, map_frame: NDArray) -> AsyncResult | NDArray:
    return upload_processing.clip(sketch_map, map_frame)


@celery.task()
def detect(sketch_map_frame: NDArray, map_frame: NDArray) -> AsyncResult | NDArray:
    return upload_processing.detect_markings(map_frame, sketch_map_frame)


@celery.task()
def img_to_geotiff(sketch_map_frame: NDArray, bbox: Bbox) -> AsyncResult | BytesIO:
    return upload_processing.img_to_geotiff(sketch_map_frame, bbox)


@celery.task()
def aggregate(*args, **kwargs) -> str:
    return BytesIO(b"Mock")
