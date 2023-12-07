from io import BytesIO

import pytest

from tests import FIXTURE_DIR


@pytest.fixture
def map_frame_markings_buffer():
    """Map frame of original Sketch Map with detected markings."""
    with open(str(FIXTURE_DIR / "map-frame-markings.png"), "rb") as file:
        return BytesIO(file.read())
