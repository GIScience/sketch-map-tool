from io import BytesIO

import qrcode
import qrcode.image.svg
from reportlab.graphics.shapes import Drawing
from svglib.svglib import svg2rlg

from sketch_map_tool import __version__
from sketch_map_tool.models import Bbox, Layer, PaperFormat


def qr_code(
    uuid: str,
    bbox: Bbox,
    layer: Layer,
    format_: PaperFormat,
    version: str = __version__,
) -> Drawing:
    """Generate a QR code holding the Celery task id and parameters of the map creation.

    :uuid: The uuid of a celery task associated with the creation of the PDF map.
    """
    data = _encode_data(uuid, bbox, layer, version)
    qr_code_svg = _make_qr_code(data)
    qr_code_rlg = _to_report_lab_graphic(format_, qr_code_svg)
    return qr_code_rlg


def _encode_data(uuid: str, bbox: Bbox, layer: Layer, version_nr: str) -> str:
    return (
        f"{version_nr},{uuid},{bbox.lon_min},"
        f"{bbox.lat_min},{bbox.lon_max},{bbox.lat_max},{layer.value}"
    )


def _make_qr_code(data: str) -> BytesIO:
    """Generate a QR code with given arguments as encoded information."""
    bytes_buffer = BytesIO()
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data(data)
    svg = qr.make_image()
    svg.save(bytes_buffer)
    bytes_buffer.seek(0)
    return bytes_buffer


def _to_report_lab_graphic(format_: PaperFormat, svg: BytesIO) -> Drawing:
    return svg2rlg(svg)
