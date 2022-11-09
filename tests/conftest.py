import pytest

from sketch_map_tool.models import Bbox, Size


@pytest.fixture
def bbox():
    return Bbox(
        964598.2387041415, 6343922.275917276, 967350.9272435782, 6346262.602545459
    )


@pytest.fixture
def size():
    return Size(width=1867, height=1587)


@pytest.fixture
def bbox_as_list():
    return [964598.2387041415, 6343922.275917276, 967350.9272435782, 6346262.602545459]


@pytest.fixture
def size_as_dict():
    return {"width": 1867, "height": 1587}
