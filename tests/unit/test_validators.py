import pytest

from sketch_map_tool.validators import (
    validate_bbox,
    validate_type,
    validate_uuid,
)


@pytest.mark.parametrize(
    "type_",
    ["sketch-map", "raster-results", "vector-results"],
)
def test_validate_type(type_):
    validate_type(type_)


@pytest.mark.parametrize("type_", ["", "foo", 3, None])
def test_validate_type_invalid(type_):
    with pytest.raises(ValueError):
        validate_type(type_)


def test_validate_uuid(uuid):
    validate_uuid(uuid)


def test_validate_uuid_invalid():
    with pytest.raises(ValueError):
        validate_uuid("")
    with pytest.raises(ValueError):
        validate_uuid("foo")


def test_validate_bbox(bbox_wgs84_str):
    validate_bbox(bbox_wgs84_str)


@pytest.mark.parametrize("bbox_str_", ["", "foo", "8.6,7.9,4.3", 3, None])
def test_validate_bbox_invalid(bbox_str_):
    with pytest.raises(ValueError):
        validate_bbox(bbox_str_)
