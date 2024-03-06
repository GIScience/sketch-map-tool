import pytest
from hypothesis import example, given
from hypothesis.strategies import text

from sketch_map_tool.config import get_config_value
from sketch_map_tool.upload_processing import ml_models
from tests import vcr_app as vcr


@pytest.mark.parametrize(
    "id",
    (
        get_config_value("neptune_model_id_yolo_osm_cls"),
        get_config_value("neptune_model_id_yolo_esri_cls"),
        get_config_value("neptune_model_id_yolo_osm_obj"),
        get_config_value("neptune_model_id_yolo_esri_obj"),
        get_config_value("neptune_model_id_sam"),
    )
)
def test_init_model(id, monkeypatch, tmpdir):
    monkeypatch.setenv("SMT-DATA-DIR", tmpdir)
    path = ml_models.init_model(id)
    assert path.is_file()


@given(text())
@example("")
@pytest.mark.skip(reason="not implemented yet")
@vcr.use_cassette
def test_init_model_unexpected_id(id):
    with pytest.raises(ValueError):
        ml_models.init_model(id)
