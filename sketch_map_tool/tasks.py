from io import BytesIO
from time import sleep
from typing import Dict, List, Union

from celery.result import AsyncResult
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from sketch_map_tool import celery_app as celery


@celery.task()
def generate_sketch_map(
    bbox: List[float],
    format_: str,
    orientation: str,
    size: Dict[str, float],
) -> Union[BytesIO, AsyncResult]:
    """Generate a sketch map as PDF."""
    sleep(10)  # simulate long running task (10s)
    buffer = BytesIO()
    canv = canvas.Canvas(buffer, pagesize=A4)
    canv.drawString(100, 100, "Sketch Map")
    canv.save()
    buffer.seek(0)
    return buffer


@celery.task()
def generate_quality_report(bbox: List[float]) -> Union[str, AsyncResult]:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    sleep(10)  # simulate long running task (10s)
    buffer = BytesIO()
    canv = canvas.Canvas(buffer, pagesize=A4)
    canv.drawString(100, 100, "Quality Report")
    canv.save()
    buffer.seek(0)
    return buffer
