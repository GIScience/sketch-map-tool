import pytest
from pytest_approval import verify, verify_image_pillow, verify_json

from sketch_map_tool.models import Bbox, Size
from sketch_map_tool.openaerialmap.client import (
    get_attribution,
    get_map_image,
    get_metadata,
)


@pytest.fixture
def item_id():
    return "59e62beb3d6412ef7220c58e"


@pytest.fixture
def size() -> Size:
    return Size(width=1716, height=1436)


@pytest.fixture
def bbox_wgs84() -> Bbox:
    return Bbox(
        *[39.22999959389618, -6.841535317101005, 39.25606520781678, -6.819872968487459]
    )


def test_get_metadata(item_id):
    verify_json(get_metadata(item_id))


def test_get_image(item_id, size, bbox_wgs84):
    image = get_map_image(item_id, size, bbox_wgs84)
    verify_image_pillow(image, extension=".png")


def test_get_image_invlaid_item_id(size, bbox_wgs84):
    get_map_image("oam:foo", size, bbox_wgs84)


def test_get_attribution(item_id):
    verify(get_attribution(item_id))
