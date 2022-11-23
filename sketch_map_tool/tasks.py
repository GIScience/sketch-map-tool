from functools import reduce
from io import BytesIO
from typing import Union

from celery.result import AsyncResult
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from sketch_map_tool import celery_app as celery
from sketch_map_tool.data_store.client import get_task_id
from sketch_map_tool.map_generation import generate_pdf as generate_map_pdf
from sketch_map_tool.map_generation.qr_code import qr_code
from sketch_map_tool.models import Bbox, File, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.upload_processing import qr_code_reader
from sketch_map_tool.wms import client as wms_client


@celery.task(bind=True)
def generate_sketch_map(
    self,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    scale: float,
) -> Union[BytesIO, AsyncResult]:
    """Generate a sketch map as PDF."""
    raw = wms_client.get_map_image(bbox, size)
    map_image = wms_client.as_image(raw)
    qr_code_ = qr_code(
        self.request.id,
        bbox,
        format_,
        orientation,
        size,
        scale,
    )
    map_pdf, map_img = generate_map_pdf(
        map_image,
        qr_code_,
        format_,
        scale,
    )
    return map_pdf, map_img


@celery.task(bind=True)
def generate_quality_report(
    self,
    bbox: Bbox,
) -> Union[BytesIO, AsyncResult]:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    report = get_report(bbox)
    return generate_report_pdf(report)


@celery.task(bind=True)
def generate_digitized_results(self, files: list[File]) -> Union[BytesIO, AsyncResult]:
    """Generate first raster data, then vector data and finally a QGIS project"""
    args = [qr_code_reader.read(file.image) for file in files]

    # all uploaded sketch maps should have the same uuid
    uuid = reduce(lambda a, b: a if a == b else None, [arg["uuid"] for arg in args])
    if uuid is None:
        raise ValueError  # TODO

    # get original map image
    task_id = get_task_id(uuid, "sketch-map")
    map_img = generate_sketch_map.AsyncResult(task_id).get()[1]

    bytes_buffer = BytesIO()
    canv = canvas.Canvas(bytes_buffer, pagesize=A4)
    canv.drawString(100, 100, "Digitized Results")
    canv.save()
    bytes_buffer.seek(0)
    return bytes_buffer
