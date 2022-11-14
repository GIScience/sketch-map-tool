import json
from dataclasses import asdict
from datetime import datetime, timezone
from io import BytesIO
from typing import List

import cv2
import qrcode
import qrcode.image.svg
from reportlab.graphics.shapes import Drawing
from svglib.svglib import svg2rlg

from sketch_map_tool import __version__
from sketch_map_tool.models import Bbox, PaperFormat, Size


def generate(
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
    data: list = _endcode_data(
        uuid,
        bbox,
        format_,
        orientation,
        size,
        version,
        timestamp,
    )
    qr_code_svg = _make(data)
    qr_code_rlg = _to_report_lab_graphic(qr_code_svg, format_.qr_scale)
    return qr_code_rlg


def detect_and_decode(img, depth=0):
    """Detect and decode QR-Code.

    If QR-Code is falsely detected but no data exists recursively down scale QR-Code
    image until data exists or maximal recursively depth is reached.

    :img:
    :depth: Maximal recursion depth
    """
    detector = cv2.QRCodeDetector()
    success, points = detector.detect(img)
    if success:
        data, _ = detector.decode(img, points)
        if data != "":
            return _decode_data(data)
        elif data == "" and depth <= 10:
            detect_and_decode(_resize(img), depth=depth + 1)
        else:
            raise Exception("Could not detect QR-Code.")
    else:
        # TODO
        if depth <= 13:
            detect_and_decode(_resize(img), depth=depth + 1)
        else:
            raise Exception("Could not detect QR-Code.")


def _endcode_data(
    uuid: str,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    version: str,
    timestamp: datetime,
) -> List[str]:
    """Encode data as text."""
    return [
        uuid,
        json.dumps(asdict(bbox)),
        format_.title,
        orientation,
        json.dumps(asdict(size)),
        version,
        timestamp.isoformat(),
    ]


def _decode_data(data):
    """Decode data as Python objects."""
    return data


def _make(data: List[str]) -> BytesIO:
    """Generate a QR code with given arguments as encoded information."""
    buffer = BytesIO()
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    for d in data:
        qr.add_data(d)
    svg = qr.make_image()
    svg.save(buffer)
    buffer.seek(0)
    return buffer


def _to_report_lab_graphic(svg: BytesIO, scale_factor: float) -> Drawing:
    rlg = svg2rlg(svg)
    rlg.scale(scale_factor, scale_factor)
    return rlg


def _resize(img, scale: float = 0.75):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    # resize image
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
