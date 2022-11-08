import json
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, List

import qrcode
import qrcode.image.svg
from svglib.svglib import svg2rlg

from sketch_map_tool import __version__


def generate_qr_code(
    uuid,
    bbox: List[float],
    format_: str,
    orientation: str,
    size: Dict[str, int],
    scale: float,
    version: str = __version__,
    timestamp: datetime = datetime.now(timezone.utc),
) -> BytesIO:
    """Generate a QR code holding the Celery task id and parameters of the map creation.

    Args:
        uuid: The uuid of a celery task associated with the creation of the PDF map.
    """
    data: list = _to_text(version, timestamp, uuid, bbox, format_, orientation, size)
    qr_code = _make_qr_code(data)
    return _as_report_lab_graphic(qr_code, scale)


def _to_text(
    version,
    timestamp,
    uuid,
    bbox: List[float],
    format_: str,
    orientation: str,
    size: Dict[str, int],
) -> List[str]:
    return [
        version,
        timestamp.isoformat(),
        str(uuid),
        json.dumps(bbox),
        format_,
        orientation,
        json.dumps(size),
    ]


def _make_qr_code(data: List[str]) -> BytesIO:
    """Generate a QR code with given arguments as encoded informations.

    The QR code is written to an in-memory bytes buffer."""
    buffer = BytesIO()
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    for d in data:
        qr.add_data(d)
    svg = qr.make_image()
    svg.save(buffer)
    buffer.seek(0)
    return buffer


def _as_report_lab_graphic(svg, scale):
    rlg = svg2rlg(svg)
    # TODO: Use scale of PaperFormat class
    rlg.scale(scale, scale)
    return rlg
