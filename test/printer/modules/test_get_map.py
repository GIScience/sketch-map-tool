"""
Tests for the module printer/modules/get_map.py
"""
import PIL
from typing import BinaryIO
from unittest.mock import patch
from helper_modules.bbox_utils import Bbox
from printer.modules.get_map import get_map_image
from constants import TIMEOUT_REQUESTS


class DummyResponse:  # pylint: disable=R0903
    """
    Dummy response to be used in mocks for request.get, which require a response with the attribute
    'raw'
    """
    def __init__(self, raw_data: BinaryIO):
        self.raw = raw_data


def test_get_map_image() -> None:
    """
    Test for the function get_map_image() with a mock for the request to the WMS.
    """
    bbox = Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373")
    with patch("requests.get") as mock:
        mock.return_value = DummyResponse(
            open("../test_data/dummy_map_img.jpg", "rb"))  # pylint: disable=R1732
        img = get_map_image(bbox, 500, 500,
                            wms_service_base_url="https://my_wms.com/wms?SERVICE=WMS&VERSION=2.0",
                            wms_layers="coolest_layer")
    mock.assert_called_once_with("https://my_wms.com/wms?SERVICE=WMS&VERSION=2.0",
                                 {
                                     "REQUEST": "GetMap",
                                     "FORMAT": "image%2Fpng",
                                     "TRANSPARENT": "FALSE",
                                     "LAYERS": "coolest_layer",
                                     "WIDTH": 500,
                                     "HEIGHT": 500,
                                     "SRS": "EPSG%3A4326",
                                     "STYLES": "",
                                     "BBOX": "8.66100311,49.3957813,8.7166214,49.4265373",
                                 }, stream=True, timeout=TIMEOUT_REQUESTS
                                 )
    assert isinstance(img, PIL.PngImagePlugin.PngImageFile)
