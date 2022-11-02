import pytest

from sketch_map_tool.helper_modules.bbox_utils import Bbox


@pytest.fixture
def bbox():
    return Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373")
