from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from sketch_map_tool import helpers


def test_get_project_root():
    expected = Path(__file__).resolve().parent.parent.parent.resolve()
    result = helpers.get_project_root()
    assert expected == result


@pytest.mark.parametrize(
    ("max_length", "width_exp", "height_exp"),
    [
        (1450, 1450, 1232),  # One dimension too big
        (1000, 1000, 850),  # Both dimensions too big
        (1456, 1456, 1238),  # Not too big, exactly limit
        (1600, 1456, 1238),  # Not too big, smaller than limit
    ],
)
def test_resize_png(map_frame_buffer, max_length, width_exp, height_exp):
    img = Image.open(map_frame_buffer)
    img_rotated = img.rotate(90, expand=1)
    width, height = img.width, img.height
    width_rotated, height_rotated = img_rotated.width, img_rotated.height
    assert width == 1456 and height == 1238
    assert width_rotated == 1238 and height_rotated == 1456

    img_rotated_buffer = BytesIO()
    img_rotated.save(img_rotated_buffer, format="png")
    img_rotated_buffer.seek(0)

    img_resized_buffer = helpers.resize_png(map_frame_buffer, max_length=max_length)
    img_rotated_resized_buffer = helpers.resize_png(
        img_rotated_buffer, max_length=max_length
    )
    img_resized = Image.open(img_resized_buffer)
    img_rotated_resized = Image.open(img_rotated_resized_buffer)

    width_resized, height_resized = img_resized.width, img_resized.height
    width_rotated_resized, height_rotated_resized = (
        img_rotated_resized.width,
        img_rotated_resized.height,
    )

    assert width_resized == width_exp and height_resized == height_exp
    assert width_rotated_resized == height_exp and height_rotated_resized == width_exp
