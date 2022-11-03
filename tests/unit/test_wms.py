from PIL.PngImagePlugin import PngImageFile

from sketch_map_tool.wms import client
from tests import vcr_app as vcr


@vcr.use_cassette()
def test_get_map_image(bbox, size):
    response = client.get_map_image(bbox, size["width"], size["height"])
    assert response.status_code == 200


@vcr.use_cassette()
def test_as_image(bbox, size):
    response = client.get_map_image(bbox, size["width"], size["height"])
    image = client.as_image(response)
    assert isinstance(image, PngImageFile)
