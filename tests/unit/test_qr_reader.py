import cv2
import pytest

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.upload_processing import qr_reader
from tests import FIXTURE_DIR

QR_CODES_FIXTURE_DIR = FIXTURE_DIR / "qr-codes"


@pytest.fixture
def qr_code_img():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code.png"))


@pytest.fixture
def qr_code_img_big():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-big.png"))


@pytest.fixture
def qr_code_img_mutliple():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-multiple.png"))


@pytest.fixture
def qr_code_img_no():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-no.png"))


@pytest.fixture
def qr_code_sketch_map():
    return cv2.imread(str(QR_CODES_FIXTURE_DIR / "qr-code-sketch-map.png"))


def test_read_qr_code(qr_code_img):
    # Too manually check the image uncomment following code.
    # cv2.imshow('image', qr_code_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    assert qr_reader.read(qr_code_img) == "Sketch Map Tool"


def test_read_qr_code_sketch_map(qr_code_sketch_map):
    assert (
        qr_reader.read(qr_code_sketch_map)
        == '90b3345b-36cf-42ef-8bcc-c1b4cf0f8473{"lat_min": 965015.9352927138, "lon_min": 6344342.122209794, "lat_max": 967072.4894825463, "lon_max": 6346090.619231817}a4landscape{"width": 1867, "height": 1587}0.9.02022-11-14T15:54:36.109466+00:00'
    )


# TODO: Fixture does not need to be down scaled.
def test_read_qr_code_big(qr_code_img_big):
    """Test reading a QR-Code image which size is too big and need to be down-scaled ...

    ... before content can be detected.
    """
    assert qr_reader.read(qr_code_img_big) == "Sketch Map Tool"


def test_read_qr_code_multiple(qr_code_img_mutliple):
    with pytest.raises(QRCodeError):
        qr_reader.read(qr_code_img_mutliple)


def test_read_qr_code_no(qr_code_img_no):
    with pytest.raises(QRCodeError):
        qr_reader.read(qr_code_img_no)


def test_resize(qr_code_sketch_map):
    resized = qr_reader._resize(qr_code_sketch_map)
    assert int(qr_code_sketch_map.shape[0] * 0.75) == resized.shape[0]
    assert int(qr_code_sketch_map.shape[1] * 0.75) == resized.shape[1]
