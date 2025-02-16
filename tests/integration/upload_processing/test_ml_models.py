import pytest
from hypothesis import example, given
from hypothesis.strategies import text

from sketch_map_tool.config import get_config_value
from sketch_map_tool.upload_processing import ml_models


@pytest.mark.parametrize(
    "id",
    (
        get_config_value("yolo_osm_cls"),
        get_config_value("yolo_esri_cls"),
        get_config_value("yolo_osm_obj"),
        get_config_value("yolo_esri_obj"),
    ),
)
def test_init_model(id):
    path = ml_models.init_model(id)
    assert path.is_file()


@given(text())
@example("")
def test_init_model_unexpected_id(id):
    with pytest.raises(FileNotFoundError):
        ml_models.init_model(id)
