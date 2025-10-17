import json
from dataclasses import astuple
from uuid import uuid4

import pytest

from sketch_map_tool.exceptions import UUIDNotFoundError
from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def mock_tasks(monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        status = "SUCCESSFUL"
        id = uuid4()

    mock_task = MockTask()
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


@pytest.mark.usefixtures("mock_tasks")
def test_create_result_post(client, bbox, bbox_wgs84, layer):
    """Redirect to /create/results/<uuid>"""
    # TODO: use params fixture from conftest
    data = {
        "bbox": json.dumps(astuple(bbox)),
        "bboxWGS84": json.dumps(astuple(bbox_wgs84)),
        "format": "A4",
        "orientation": "landscape",
        "size": '{"width":1867,"height":1587}',
        "scale": "11545.36",
        "layer": layer,
    }
    resp = client.post("/create/results", data=data)
    assert resp.status_code == 302


def test_create_results_uuid(client, uuid, monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.get_async_result",
        lambda *_: None,
    )
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 200


def test_create_results_uuid_bbox(client, uuid, bbox_wgs84_str, monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.get_async_result",
        lambda *_: None,
    )
    resp = client.get("/create/results/{0}/{1}".format(uuid, bbox_wgs84_str))
    assert resp.status_code == 200


def test_create_results_uuid_not_found(monkeypatch, client):
    def raise_(exception):
        raise exception

    monkeypatch.setattr(
        "sketch_map_tool.routes.get_async_result",
        lambda *_: raise_(UUIDNotFoundError("")),
    )

    resp = client.get("/create/results/{0}".format(uuid4()))
    assert resp.status_code == 404


def test_create_results_invalid_uuid(client):
    uuid = "foo"
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 500


def test_create_results_invalid_bbox(client, uuid):
    bbox = "foo"
    resp = client.get("/create/results/{0}/{1}".format(uuid, bbox))
    assert resp.status_code == 500
