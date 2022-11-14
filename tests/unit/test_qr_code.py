from datetime import datetime
from io import BytesIO, StringIO
from uuid import uuid4

import cv2
import pytest
from reportlab.graphics.shapes import Drawing

from sketch_map_tool.qr_code.qr_code import (
    _endcode_data,
    _make,
    _resize,
    _to_report_lab_graphic,
    detect_and_decode,
    generate,
)
from tests import FIXTURE_DIR


@pytest.fixture
def sketch_map():
    return cv2.imread(str(FIXTURE_DIR / "sketch-map.png"))


@pytest.fixture
def qr_code_img():
    return cv2.imread(str(FIXTURE_DIR / "qr-code.png"))


@pytest.fixture
def qr_code_img_big():
    return cv2.imread(str(FIXTURE_DIR / "qr-code-big.png"))


def test_encode_data(bbox, format_, size):
    result = _endcode_data(
        str(uuid4()),
        bbox,
        format_,
        "landscape",
        size,
        "0.1.0",
        datetime.now(),
    )
    for element in result:
        assert isinstance(element, str)


def test_make():
    result = _make(["foo", "bar"])
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


def test_generate(
    bbox,
    format_,
    size,
):
    result = generate(
        str(uuid4()),
        bbox,
        format_,
        "landscape",
        size,
        75,
    )
    assert isinstance(result, Drawing)


def test_resize(qr_code_img):
    qr_code_resized = _resize(qr_code_img)
    assert int(qr_code_img.shape[0] * 0.75) == qr_code_resized.shape[0]
    assert int(qr_code_img.shape[1] * 0.75) == qr_code_resized.shape[1]


def test_detect_and_decode(qr_code_img):
    # Too manually check the image uncomment following code.
    # cv2.imshow('image', qr_code_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    detect_and_decode(qr_code_img)


def test_detect_and_decode_sketch_map(sketch_map):
    detect_and_decode(sketch_map)


def test_read_detect_and_decode_success(qr_code_img_big):
    """Test reading a QR-Code image which size is too big and need to be down-scaled ...

    ... before content can be detected.
    """
    detect_and_decode(qr_code_img_big)


def test_read_detect_and_decode_failure(qr_code_img_big):
    with pytest.raises(Exception):
        detect_and_decode(qr_code_img_big, depth=11)
