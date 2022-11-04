from datetime import datetime
from io import BytesIO, StringIO
from uuid import uuid4

from reportlab.graphics.shapes import Drawing

from sketch_map_tool.map_generation import qr_code


def test_to_text():
    result = qr_code._to_text(
        "0.1.0",
        datetime.now(),
        uuid4(),
        [0.0, 0.0, 0.0, 0.0],
        "a4",
        "landscape",
        {"width": 500, "height": 200},
    )
    for element in result:
        assert isinstance(element, str)


def test_make_qr_code():
    result = qr_code._make_qr_code(["foo", "bar"])
    assert isinstance(result, BytesIO)


def test_as_report_lab_graphic():
    buffer = StringIO()
    buffer.write(
        """
<svg width="100" height="100">
   <circle cx="50" cy="50" r="40"/>
</svg>
"""
    )
    buffer.seek(0)
    result = qr_code._as_report_lab_graphic(buffer, "a4")
    assert isinstance(result, Drawing)


def test_generate_qr_code():
    result = qr_code.generate_qr_code(
        uuid4(), [0.0, 0.0, 0.0, 0.0], "a4", "landscape", {"width": 500, "height": 200}
    )
    assert isinstance(result, Drawing)
