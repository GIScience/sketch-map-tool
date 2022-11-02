"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

from sketch_map_tool import tasks


def test_generate_map(monkeypatch):
    monkeypatch.setattr("sketch_map_tool.tasks.sleep", lambda x: None)
    result = tasks.generate_map([], "", "", {})
    assert isinstance(result, BytesIO)


def test_generate_quality_report(monkeypatch):
    monkeypatch.setattr("sketch_map_tool.tasks.sleep", lambda x: None)
    result = tasks.generate_quality_report([])
    assert isinstance(result, BytesIO)
