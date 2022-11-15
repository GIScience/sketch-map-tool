import pathlib

import cv2
import pytest

from sketch_map_tool.upload_processing import qr_reader

input_img_dir = pathlib.Path(__file__).parent.parent.resolve() / "test_data"


def test_read():
    img = cv2.imread(str(input_img_dir / "1_qr.jpg"))
    assert (
        qr_reader.read(img)
        == "-67.8323439,-9.99624296,-67.7974215,-9.96700015;2022-11-10;a4"
    )


def test_read_2_equal_codes():
    img = cv2.imread(str(input_img_dir / "2_qr_same.jpg"))
    assert (
        qr_reader.read(img)
        == "-67.8323439,-9.99624296,-67.7974215,-9.96700015;2022-11-10;a4"
    )


def test_read_2_different_codes():
    img = cv2.imread(str(input_img_dir / "2_qr_different.jpg"))
    with pytest.raises(qr_reader.MultipleDifferentQRCodesException):
        qr_reader.read(img)


def test_read_no_codes():
    img = cv2.imread(str(input_img_dir / "no_code.jpg"))
    with pytest.raises(qr_reader.NoQRCodeException):
        qr_reader.read(img)
