from io import BytesIO
from time import sleep
from typing import List, Union

from celery.result import AsyncResult
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from sketch_map_tool import celery_app as celery
from sketch_map_tool.map_generation import generate_pdf
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.qr_code import qr_code
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
    qr_code_ = qr_code.generate(
        self.request.id,
        bbox,
        format_,
        orientation,
        size,
    )
    map_pdf, _ = generate_pdf(
        map_image,
        qr_code_,
        format_,
        scale,
    )
    return map_pdf


@celery.task(bind=True)
def generate_quality_report(
    self,
    bbox: List[float],
) -> Union[BytesIO, AsyncResult]:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    print(self.request.id)
    sleep(10)  # simulate long running task (10s)
    buffer = BytesIO()
    canv = canvas.Canvas(buffer, pagesize=A4)
    canv.drawString(100, 100, "Quality Report")
    canv.save()
    buffer.seek(0)
    return buffer


@celery.task(bind=True)
def generate_digitized_results(self, files) -> Union[BytesIO, AsyncResult]:
    """Generate first raster data, then vector data and finally a QGIS project"""
    print(self.request.id)
    print(files[0]["filename"])
    sleep(3)  # simulate long running task (3s)
    buffer = BytesIO()
    canv = canvas.Canvas(buffer, pagesize=A4)
    canv.drawString(100, 100, "Digitized Results")
    canv.drawImage(ImageReader(files[0]["bytes"]), 100, 120, 400, None, None, True)
    canv.save()
    buffer.seek(0)
    return buffer
