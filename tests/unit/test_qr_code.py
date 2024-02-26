from io import BytesIO
from uuid import uuid4

from reportlab.graphics.shapes import Drawing

from sketch_map_tool.map_generation.qr_code import (
    _encode_data,
    _make_qr_code,
    _to_report_lab_graphic,
    qr_code,
)


def test_encode_data(bbox, format_, size, scale, uuid):
    result = _encode_data(
        uuid,
        bbox,
        "0.1.0",
    )
    assert isinstance(result, str)


def test_make_qr_code():
    result = _make_qr_code(["foo", "bar"])
    assert isinstance(result, BytesIO)


def test_to_report_lab_graphic(format_):
    input_string = """
<svg width="100" height="100">
   <circle cx="50" cy="50" r="40"/>
</svg>
"""
    bytes_buffer = BytesIO(input_string.encode())
    result = _to_report_lab_graphic(format_, bytes_buffer)
    assert isinstance(result, Drawing)


def test_qr_code(
    bbox,
    format_,
    size,
):
    result = qr_code(
        str(uuid4()),
        bbox,
        format_,
    )
    assert isinstance(result, Drawing)
