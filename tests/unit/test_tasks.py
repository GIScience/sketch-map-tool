"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

import pytest

from sketch_map_tool import tasks
from tests import vcr_app as vcr


@pytest.fixture
def mock_task(monkeypatch, uuid):
    """Mock celery tasks results."""

    class MockTask:
        status = "SUCCESSFUL"

        def __init__(self, task_id):
            self.id = task_id

        def get(self):
            return [0, 1]

    mock_task = MockTask(uuid)
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_sketch_map.AsyncResult",
        lambda args: mock_task,
    )


@pytest.fixture
def mock_get_task_id(monkeypatch, uuid):
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.get_task_id", lambda id_, field: uuid
    )


@vcr.use_cassette
def test_generate_sketch_map(monkeypatch, uuid, bbox, format_, size, scale, layer):
    monkeypatch.setattr(
        "sketch_map_tool.tasks.db_client_celery.insert_map_frame",
        lambda *_: uuid,
    )
    map_pdf = tasks.generate_sketch_map(
        uuid,
        bbox,
        format_,
        "landscape",
        size,
        scale,
        layer,
    )
    assert isinstance(map_pdf, BytesIO)


@vcr.use_cassette
def test_generate_quality_report(bbox_wgs84):
    result = tasks.generate_quality_report(bbox_wgs84)
    assert isinstance(result, BytesIO)
