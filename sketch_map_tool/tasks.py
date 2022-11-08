from io import BytesIO
from time import sleep
from typing import Dict, List, Union

from celery.result import AsyncResult
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.datastructures import FileStorage

from sketch_map_tool import celery_app as celery
from sketch_map_tool.wms import client as wms_client


@celery.task(bind=True)
def generate_sketch_map(
    self,
    bbox: List[float],
    format_: str,
    orientation: str,
    size: Dict[str, float],
) -> Union[BytesIO, AsyncResult]:
    """Generate a sketch map as PDF."""
    print(size)
    raw = wms_client.get_map_image(bbox, size["width"], size["height"])
    map_image = wms_client.as_image(raw)

    buffer = BytesIO()
    map_image.save(buffer, format="png")
    buffer.seek(0)
    return buffer


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
def generate_digitized_results(
    self, files: List[FileStorage]
) -> Union[BytesIO, AsyncResult]:
    """Generate first raster data, then vector data and finally a QGIS project"""
    print(self.request.id)
    sleep(3)  # simulate long running task (3s)
    buffer = BytesIO()
    canv = canvas.Canvas(buffer, pagesize=A4)
    canv.drawString(100, 100, "Digitized Results")
    canv.save()
    buffer.seek(0)
    return buffer
