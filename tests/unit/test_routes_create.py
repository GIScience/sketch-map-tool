import json
from dataclasses import astuple
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def mock_tasks(monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        id = uuid4()

    mock_task = MockTask()
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_quality_report.apply_async",
        lambda args: mock_task,
    )
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_sketch_map.apply_async",
        lambda args: mock_task,
    )


def test_create(client):
    resp = client.get("/create")
    assert resp.status_code == 200


def test_create_result_get(client):
    """Redirect to /create"""
    resp = client.get("/create/results")
    assert resp.status_code == 302  # Redirect


def test_create_result_post(client, mock_tasks, monkeypatch, bbox, bbox_wgs84):
    """Redirect to /create/results/<uuid>"""
    monkeypatch.setattr(
        "sketch_map_tool.database.client.set_async_result_ids", lambda x, y: None
    )
    data = {
        "bbox": json.dumps(astuple(bbox)),
        "bboxWGS84": json.dumps(astuple(bbox_wgs84)),
        "format": "A4",
        "orientation": "landscape",
        "size": '{"width":1867,"height":1587}',
        "scale": "11545.36",
    }
    resp = client.post("/create/results", data=data)
    assert resp.status_code == 302


def test_create_results_uuid(client, uuid, monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.db_client.get_async_result_id", lambda a, b: None
    )
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 200


@patch("sketch_map_tool.database.client.db_conn")
def test_create_results_uuid_not_found(mock_conn, client, uuid):
    mock_curs = MagicMock()
    mock_curs.fetchall.return_value = []
    mock_conn.cursor.return_value.__enter__.return_value = mock_curs

    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 404


def test_create_results_invalid_uuid(client):
    uuid = "foo"
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 500
