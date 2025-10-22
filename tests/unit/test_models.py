import pytest

from sketch_map_tool import models
from sketch_map_tool.exceptions import ValidationError


@pytest.fixture
def bbox_as_list() -> list:
    return [964472.1973848869, 6343459.035638228, 967434.6098457306, 6345977.635778541]


def test_bbox(bbox_as_list):
    bbox = models.Bbox(*bbox_as_list)
    assert bbox.lon_min == 964472.1973848869
    assert bbox.lat_min == 6343459.035638228
    assert bbox.lon_max == 967434.6098457306
    assert bbox.lat_max == 6345977.635778541


def test_bbox_str(bbox_as_list):
    bbox = models.Bbox(*bbox_as_list)
    assert (
        str(bbox)
        == "964472.1973848869,6343459.035638228,967434.6098457306,6345977.635778541"
    )


def test_bbox_centroid(bbox_as_list):
    bbox = models.Bbox(*bbox_as_list)
    expected_centroid = (965953.4036153087, 6344718.335708384)
    assert bbox.centroid == expected_centroid
    assert isinstance(bbox.centroid, tuple)


def test_size(size_as_dict):
    size = models.Size(**size_as_dict)
    assert size.width == 1867
    assert size.height == 1587


def test_literatur_reference():
    literature_reference = models.LiteratureReference(
        img_src="ijgi-10-00130-g002.webp",
        citation="Klonner, C., Hartmann, M., Dischl, R., Djami, L., Anderson, L.,"
        " Raifer, M., Lima-Silva, F., Degrossi, L. C.,"
        " Zipf, A., de Albuquerque, J. P. (2021): "
        "The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data"
        " for Participatory Mapping,"
        " 10(3): 130. ISPRS International Journal of Geo-Information. 10:130.",
        url="https://doi.org/10.3390/ijgi10030130",
    )
    assert literature_reference.img_src == "ijgi-10-00130-g002.webp"
    assert literature_reference.citation == (
        "Klonner, C., Hartmann, M., Dischl, R., Djami, L., Anderson, L.,"
        " Raifer, M., Lima-Silva, F., Degrossi, L. C., Zipf, A.,"
        " de Albuquerque, J. P. (2021):"
        " The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data"
        " for Participatory Mapping, 10(3): 130. "
        "ISPRS International Journal of Geo-Information. 10:130."
    )
    assert literature_reference.url == "https://doi.org/10.3390/ijgi10030130"


def test_layer(layer):
    assert models.validate_layer(layer)


def test_layer_invalid():
    with pytest.raises(ValidationError):
        models.validate_layer("foo")


@pytest.mark.skip
def test_layer_invalid_():
    # TODO: Validate does not catch non-existing OAM item IDs
    with pytest.raises(ValidationError):
        models.validate_layer("oam:foo")
