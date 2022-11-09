"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

from sketch_map_tool import tasks
from tests import vcr_app as vcr


@vcr.use_cassette()
def test_generate_sketch_map(monkeypatch, bbox, size):
    result = tasks.generate_sketch_map(bbox, "", "", size, 0.0)
    assert isinstance(result, BytesIO)


@vcr.use_cassette()
def test_generate_quality_report(monkeypatch):
    monkeypatch.setattr("sketch_map_tool.tasks.sleep", lambda x: None)
    result = tasks.generate_quality_report([])
    assert isinstance(result, BytesIO)
