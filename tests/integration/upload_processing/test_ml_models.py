import pytest
from hypothesis import example, given
from hypothesis.strategies import text

from sketch_map_tool.config import CONFIG
from sketch_map_tool.upload_processing import ml_models


@pytest.mark.parametrize(
    "id",
    (
        CONFIG.yolo_osm_obj,
        CONFIG.yolo_esri_obj,
        CONFIG.yolo_cls,
    ),
)
def test_init_model(id):
    path = ml_models.init_model(id)
    assert path.is_file()


@given(
    text().filter(
        lambda n: n
        not in (
            CONFIG.yolo_osm_obj,
            CONFIG.yolo_esri_obj,
            CONFIG.yolo_cls,
        )
    )
)
@example("")
def test_init_model_unexpected_id(id):
    # ValueError: PosixPath('/') has an empty name
    with pytest.raises((FileNotFoundError, OSError, ValueError)):
        ml_models.init_model(id)
