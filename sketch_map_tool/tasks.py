from io import BytesIO
from typing import Union
from zipfile import ZipFile

from celery.result import AsyncResult

from sketch_map_tool import celery_app as celery
from sketch_map_tool.map_generation import generate_pdf as generate_map_pdf
from sketch_map_tool.map_generation.qr_code import qr_code
from sketch_map_tool.models import Bbox, File, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.upload_processing import map_cutter
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
def generate_digitized_results(
    self, files: list[File], map_img: BytesIO
) -> Union[BytesIO, AsyncResult]:
    """Generate first raster data, then vector data and finally a QGIS project"""
    # cut out map frame
    map_frames = [map_cutter.cut_out_map(file.image, map_img) for file in files]

    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for file, map_frame in zip(files, map_frames):
            zip_file.writestr(file.filename + ".txt", map_frame)
    buffer.seek(0)
    return buffer
