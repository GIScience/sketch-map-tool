from uuid import uuid4

import pytest

from sketch_map_tool.models import Bbox, PaperFormat, Size


@pytest.fixture
def bbox():
    return Bbox(
        966492.364208868,
        6343445.659216596,
        969486.2275163643,
        6345991.012200175,
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
    return 1283.129


@pytest.fixture
def uuid():
    return str(uuid4())


@pytest.fixture
def bbox_as_list():
    return [964598.2387041415, 6343922.275917276, 967350.9272435782, 6346262.602545459]


@pytest.fixture
def size_as_dict():
    return {"width": 1867, "height": 1587}
