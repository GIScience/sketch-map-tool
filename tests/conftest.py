from io import BytesIO

import cv2
import pytest

from sketch_map_tool.models import Bbox, PaperFormat, Size
from tests import FIXTURE_DIR


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
    return PaperFormat(
        "a4",
        width=29.7,
        height=21,
        right_margin=5,
        font_size=8,
        qr_scale=0.6,
        compass_scale=0.25,
        globe_scale=0.125,
        scale_height=0.33,
        qr_y=0.1,
        indent=0.25,
        qr_contents_distances_not_rotated=(2, 3),
        qr_contents_distance_rotated=3,
    )


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


@pytest.fixture
def sketch_map_buffer():
    """Photo of a Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def map_frame_buffer():
    """Map frame of original Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map-frame.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map():
    """Photo of a Sketch Map."""
    return cv2.imread(
        str(FIXTURE_DIR / "sketch-map.png"), cv2.IMREAD_COLOR
    )  # BGR color format and no alpha channel


@pytest.fixture
def map_frame():
    """Map frame of original Sketch Map."""
    return cv2.imread(str(FIXTURE_DIR / "sketch-map-frame.png"))


# @pytest.fixture
# def file(sketch_map):
#     return File(filename="filename", mimetype="image/png", image=sketch_map)


# @pytest.fixture
# def files(file):
#     return [file, file]
