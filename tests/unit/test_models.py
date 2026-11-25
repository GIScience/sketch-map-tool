import base64
import json
from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError
from shapely.geometry import Point

from sketch_map_tool import models
from sketch_map_tool.models import Legend, LegendEntry, legend_entries_adapter


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
    assert isinstance(bbox.centroid, Point)
    assert bbox.centroid.wkt == "POINT (965953.4036153088 6344718.3357083835)"


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


def _png_data_url(size=(4, 4)) -> str:
    buffer = BytesIO()
    Image.new("RGBA", size).save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def _legend_entry(**kwargs) -> dict:
    return {
        "color": "blue",
        "hex": "#0E6EB8",
        "type": "point",
        "count": 3,
        "label": "blue",
        "image": _png_data_url(),
        "width": 20,
        "height": 30,
        **kwargs,
    }


def test_legend_entry():
    entry = LegendEntry(**_legend_entry())
    assert entry.image_bytes().startswith(b"\x89PNG")


def test_legend_entry_without_image():
    entry = LegendEntry(**_legend_entry(image=""))
    assert entry.image_bytes() is None


@pytest.mark.parametrize(
    "image",
    [
        "data:image/jpeg;base64,AAAA",
        "data:image/png;base64,not base64!",
        "data:image/png;base64," + base64.b64encode(b"GIF89a").decode(),
        "data:image/png;base64," + "A" * 300_000,
    ],
)
def test_legend_entry_invalid_image(image):
    with pytest.raises(ValidationError):
        LegendEntry(**_legend_entry(image=image))


def test_legend_entries_from_json():
    entries = legend_entries_adapter.validate_json(json.dumps([_legend_entry()]))
    legend = Legend(title="Title", entries=entries)
    assert legend.entries[0].label == "blue"


def test_legend_entries_too_many():
    with pytest.raises(ValidationError):
        legend_entries_adapter.validate_json(json.dumps([_legend_entry()] * 51))
