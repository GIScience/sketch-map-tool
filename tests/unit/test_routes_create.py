from uuid import UUID, uuid4

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
        "sketch_map_tool.routes.tasks.generate_map.apply_async",
        lambda args: mock_task,
    )


def test_create(client):
    resp = client.get("/create")
    assert resp.status_code == 200


def test_create_result_get(client):
    """Redirect to /create"""
    resp = client.get("/create/results")
    assert resp.status_code == 302  # Redirect


def test_create_result_post(client, mock_tasks, monkeypatch):
    """Redirect to /create/results/<uuid>"""
    monkeypatch.setattr("sketch_map_tool.data_store.client.set", lambda x: None)
    data = {
        "bbox": "[965172.1534546925,6343953.965425534,966970.2550592694,6345482.705991237]",
        "format": "A4",
        "orientation": "landscape",
        "size": '{"width":1867,"height":1587}',
    }
    resp = client.post("/create/results", data=data)
    assert resp.status_code == 302


def test_create_results_uuid(client):
    uuid = "16fd2706-8baf-433b-82eb-8c7fada847da"
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 200


def test_create_results_uuid_not_found(client):
    uuid = "16fd2706-8baf-433b-82eb-8c7fada847db"
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 200
    # TODO: Should be 404
    # assert resp.status_code == 404


def test_create_results_invalid_uuid(client):
    uuid = "foo"
    resp = client.get("/create/results/{0}".format(uuid))
    assert resp.status_code == 500
