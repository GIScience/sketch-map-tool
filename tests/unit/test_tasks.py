"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

import numpy as np
import pytest

from sketch_map_tool import tasks
from tests import vcr_app as vcr


@pytest.fixture()
def mock_task(monkeypatch, uuid):
    """Mock celery tasks results."""

    class MockTask:
        def __init__(self, task_id):
            self.id = task_id

        def get(self):
            return [0, 1]

    mock_task = MockTask(uuid)
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_sketch_map.AsyncResult",
        lambda args: mock_task,
    )


@pytest.fixture()
def mock_get_task_id(monkeypatch, uuid):
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.get_task_id", lambda id_, field: uuid
    )


@vcr.use_cassette()
def test_generate_sketch_map(monkeypatch, bbox, format_, size, scale):
    map_pdf, map_img = tasks.generate_sketch_map(
        bbox, format_, "landscape", size, scale
    )
    assert isinstance(map_pdf, BytesIO)
    assert isinstance(map_img, BytesIO)


@vcr.use_cassette("test_get_report")
def test_generate_quality_report(bbox_wgs84):
    result = tasks.generate_quality_report(bbox_wgs84)
    assert isinstance(result, BytesIO)


def test_clip(sketch_map, map_frame):
    result = tasks.t_clip(sketch_map, map_frame)
    assert isinstance(result, np.ndarray)


def test_img_to_geotiff(map_frame, bbox):
    result = tasks.t_georeference(map_frame, bbox)
    assert isinstance(result, BytesIO)
