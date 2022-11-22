"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

from sketch_map_tool import tasks
from tests import vcr_app as vcr


@vcr.use_cassette()
def test_generate_sketch_map(monkeypatch, bbox, format_, size, scale):
    result = tasks.generate_sketch_map(bbox, format_, "landscape", size, scale)
    assert isinstance(result, BytesIO)


@vcr.use_cassette("test_get_report")
def test_generate_quality_report(monkeypatch, bbox_wgs84):
    monkeypatch.setattr("sketch_map_tool.tasks.sleep", lambda x: None)
    result = tasks.generate_quality_report(bbox_wgs84)
    assert isinstance(result, BytesIO)
