import pathlib

import cv2
import pytest

from sketch_map_tool.upload_processing import qr_reader
from tests import FIXTURE_DIR


@pytest.fixture
def img_one_code():
    return cv2.imread(str(FIXTURE_DIR / "qr-code-1-code.jpg"))


@pytest.fixture
def img_two_equal_codes():
    return cv2.imread(str(FIXTURE_DIR / "qr-code-2-same-codes.jpg"))


@pytest.fixture
def img_two_different_codes():
    return cv2.imread(str(FIXTURE_DIR / "qr-code-2-different-codes.jpg"))


@pytest.fixture
def img_no_code():
    return cv2.imread(str(FIXTURE_DIR / "qr-code-no-code.jpg"))


def test_read(img_one_code):
    assert (
        qr_reader.read(img_one_code)
        == "-67.8323439,-9.99624296,-67.7974215,-9.96700015;2022-11-10;a4"
    )


def test_read_2_equal_codes(img_two_equal_codes):
    assert (
        qr_reader.read(img_two_equal_codes)
        == "-67.8323439,-9.99624296,-67.7974215,-9.96700015;2022-11-10;a4"
    )


def test_read_2_different_codes(img_two_different_codes):
    with pytest.raises(qr_reader.MultipleDifferentQRCodesException):
        qr_reader.read(img_two_different_codes)


def test_read_no_codes(img_no_code):
    with pytest.raises(qr_reader.NoQRCodeException):
        qr_reader.read(img_no_code)
