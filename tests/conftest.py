import pytest

from sketch_map_tool.definitions import A4
from sketch_map_tool.models import Bbox, Size


@pytest.fixture
def bbox():
    return Bbox(
        lon_min=964472.1973848869,
        lat_min=6343459.035638228,
        lon_max=967434.6098457306,
        lat_max=6345977.635778541,
    )


@pytest.fixture
def size():
    return Size(width=1867, height=1587)


@pytest.fixture
def format_():
    return A4


@pytest.fixture
def scale():
    return 10231.143861780083


@pytest.fixture
def uuid():
    return "654dd0d3-7bb0-4a05-8a68-517f0d9fc98e"


@pytest.fixture
def bbox_as_list():
    return [964472.1973848869, 6343459.035638228, 967434.6098457306, 6345977.635778541]


@pytest.fixture
def bbox_wgs84():
    return Bbox(lon_min=8.625, lat_min=49.3711, lon_max=8.7334, lat_max=49.4397)


@pytest.fixture
def size_as_dict():
    return {"width": 1867, "height": 1587}
