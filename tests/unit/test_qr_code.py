import json
from datetime import datetime
from io import BytesIO, StringIO
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
        format_,
        "landscape",
        size,
        scale,
        "0.1.0",
        datetime.now(),
    )
    assert isinstance(result, str)
    assert isinstance(json.loads(result), dict)


def test_make_qr_code():
    result = _make_qr_code(["foo", "bar"])
    assert isinstance(result, BytesIO)


def test_to_report_lab_graphic():
    buffer = StringIO()
    buffer.write(
        """
<svg width="100" height="100">
   <circle cx="50" cy="50" r="40"/>
</svg>
"""
    )
    buffer.seek(0)
    result = _to_report_lab_graphic(buffer, 0.75)
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
        "landscape",
        size,
        75,
    )
    assert isinstance(result, Drawing)
