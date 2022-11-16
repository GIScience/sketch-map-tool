import json
from dataclasses import asdict
from datetime import datetime, timezone
from io import BytesIO
from typing import List

import qrcode
import qrcode.image.svg
from reportlab.graphics.shapes import Drawing
from svglib.svglib import svg2rlg

from sketch_map_tool import __version__
from sketch_map_tool.models import Bbox, PaperFormat, Size


def qr_code(
    uuid: str,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    version: str = __version__,
    timestamp: datetime = datetime.now(timezone.utc),
) -> Drawing:
    """Generate a QR code holding the Celery task id and parameters of the map creation.

    :uuid: The uuid of a celery task associated with the creation of the PDF map.
    """
    data = _encode_data(
        uuid,
        bbox,
        format_,
        orientation,
        size,
        version,
        timestamp,
    )
    qr_code_svg = _make_qr_code(data)
    qr_code_rlg = _to_report_lab_graphic(qr_code_svg, format_.qr_scale)
    return qr_code_rlg


def _encode_data(
    uuid: str,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    version: str,
    timestamp: datetime,
) -> List[str]:
    return json.dumps(
        {
            "id": uuid,
            "bbox": asdict(bbox),
            "format": format_.title,
            "orientation": orientation,
            "size": asdict(size),
            "version": version,
            "timestamp": timestamp.isoformat(),
        }
    )


def _make_qr_code(data: str) -> BytesIO:
    """Generate a QR code with given arguments as encoded information."""
    buffer = BytesIO()
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data(data)
    svg = qr.make_image()
    svg.save(buffer)
    buffer.seek(0)
    return buffer


def _to_report_lab_graphic(svg: BytesIO, scale_factor: float) -> Drawing:
    rlg = svg2rlg(svg)
    rlg.scale(scale_factor, scale_factor)
    return rlg
