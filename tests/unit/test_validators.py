import pytest

from sketch_map_tool.validators import validate_type, validate_uuid


@pytest.mark.parametrize(
    "type_",
    ["quality-report", "sketch-map", "raster-results", "vector-results", "qgis-data"],
)
def test_validate_type(type_):
    validate_type(type_)


@pytest.mark.parametrize("type_", ["", "foo", 3, None])
def test_validate_type_invalid(type_):
    with pytest.raises(ValueError):
        validate_type(type_)


def test_validate_uui(uuid):
    validate_uuid(uuid)


def test_validate_uuid_invalid():
    with pytest.raises(ValueError):
        validate_uuid("")
    with pytest.raises(ValueError):
        validate_uuid("foo")
