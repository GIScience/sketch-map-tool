from types import MappingProxyType

import cv2
import pytest

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.upload_processing import qr_code_reader
from tests import FIXTURE_DIR

QR_CODES_FIXTURE_DIR = FIXTURE_DIR / "qr-codes"


@pytest.fixture
def qr_code_img():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code.png"))


@pytest.fixture
def qr_code_img_big():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-sketch-map-big.png"))


@pytest.fixture
def qr_code_img_mutliple():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-multiple.png"))


@pytest.fixture
def qr_code_img_no():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-no.png"))


@pytest.fixture
def qr_code_invalid_uuid():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-invalid-uuid.png"))


@pytest.fixture
def qr_code_invalid_contents():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-invalid-contents.jpg"))


@pytest.fixture
def decoded_content(uuid, bbox, version_nr):
    return MappingProxyType(
        {
            "uuid": uuid,
            "bbox": bbox,
            "version": version_nr,
            "layer": "osm",
        }
    )


def test_read_qr_code(qr_code_img, decoded_content):
    # Too manually check the image uncomment following code.
    # cv2.imshow('image', qr_code_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    assert qr_code_reader.read_qr_code(qr_code_img) == decoded_content


def test_read_qr_code_sketch_map(sketch_map, decoded_content):
    assert qr_code_reader.read_qr_code(sketch_map) == decoded_content


def test_read_qr_code_big(qr_code_img_big):
    """Test reading a QR-Code image which size is too big and need to be down-scaled ...

    ... before content can be detected.
    """
    assert qr_code_reader.read_qr_code(qr_code_img_big) is not None
    with pytest.raises(QRCodeError):
        qr_code_reader.read_qr_code(
            qr_code_img_big, depth=6
        )  # Disable recursion (resizing)


def test_read_qr_code_multiple(qr_code_img_mutliple):
    with pytest.raises(QRCodeError) as qr_code_error:
        qr_code_reader.read_qr_code(qr_code_img_mutliple)
    assert str(qr_code_error.value) == "Multiple QR-Codes detected."


def test_read_qr_code_no(qr_code_img_no):
    with pytest.raises(QRCodeError) as qr_code_error:
        qr_code_reader.read_qr_code(qr_code_img_no)
    assert str(qr_code_error.value) == "QR-Code could not be detected."


def test_read_qr_code_invalid_uuid(qr_code_invalid_uuid):
    with pytest.raises(QRCodeError) as qr_code_error:
        qr_code_reader.read_qr_code(qr_code_invalid_uuid)
    assert str(qr_code_error.value) == "The provided UUID is invalid."


def test_read_qr_code_invalid_contents(qr_code_invalid_contents):
    with pytest.raises(QRCodeError) as qr_code_error:
        qr_code_reader.read_qr_code(qr_code_invalid_contents)
    assert str(qr_code_error.value) == "QR-Code does not have expected content."


def test_resize(sketch_map):
    resized = qr_code_reader._resize(sketch_map)
    assert int(sketch_map.shape[0] * 0.75) == resized.shape[0]
    assert int(sketch_map.shape[1] * 0.75) == resized.shape[1]
