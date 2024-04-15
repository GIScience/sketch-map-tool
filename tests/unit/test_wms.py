from PIL.PngImagePlugin import PngImageFile

from sketch_map_tool.models import Bbox, Layer, Size
from sketch_map_tool.wms import client
from tests import vcr_app as vcr


@vcr.use_cassette
def test_get_map_image(bbox, size, layer):
    map_image = client.get_map_image(bbox, size, layer)
    # image.show()  # for showing of the image during manual testing
    assert isinstance(map_image, PngImageFile)


@vcr.use_cassette
def test_get_map(bbox, size, layer):
    response = client.get_map(bbox, size, layer)
    assert response.status_code == 200


@vcr.use_cassette
def test_as_image(bbox, size, layer):
    response = client.get_map(bbox, size, layer)
    image = client.as_image(response)
    # image.show()  # for showing of the image during manual testing
    assert isinstance(image, PngImageFile)


@vcr.use_cassette
def test_as_image_could_not_get_any_sources(bbox, size):
    """Test case covering issue described in #416.

    Without the fallback (try/except) in `get_map_image` this would lead to an Error.
    """
    layer = "esri-world-imagery"
    bbox = Bbox(
        *[
            3115430.61527546,
            859273.1634149066,
            3116705.00304079,
            860339.8395431428,
        ]
    )
    size = Size(**{"width": 1716, "height": 1436})
    layer = Layer("esri-world-imagery")
    map_image = client.get_map_image(bbox, size, layer)
    # map_image.show()  # for showing of the image during manual testing
    assert isinstance(map_image, PngImageFile)
