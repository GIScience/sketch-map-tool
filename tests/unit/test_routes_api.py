import json

import pytest
from celery.states import (
    FAILURE,
    PENDING,
    RECEIVED,
    REJECTED,
    RETRY,
    REVOKED,
    STARTED,
    SUCCESS,
)

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def uuid():
    return "16fd2706-8baf-433b-82eb-8c7fada847da"


@pytest.fixture()
def mock_request_task_mapping(request, monkeypatch):
    """Mock request id to task id mapping."""
    type_ = request.getfixturevalue("type_")
    request_task = json.dumps({type_: "16fd2706-8baf-433b-82eb-8c7fada847da"})
    monkeypatch.setattr("sketch_map_tool.routes.ds_client.get", lambda x: request_task)


@pytest.fixture()
def mock_async_results(request, monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        def __init__(self, status):
            self.status = status

    status = request.getfixturevalue("status")
    mock_task = MockTask(status)
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_quality_report.AsyncResult",
        lambda x: mock_task,
    )
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_map.AsyncResult",
        lambda x: mock_task,
    )


@pytest.mark.parametrize("status", (SUCCESS,))
@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_success(
    client,
    uuid,
    type_,
    status,
    mock_request_task_mapping,
    mock_async_results,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)


@pytest.mark.parametrize("status", (PENDING, RETRY, RECEIVED, STARTED))
@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_processing(
    client,
    uuid,
    type_,
    status,
    mock_request_task_mapping,
    mock_async_results,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.json["id"] == uuid
    assert resp.json["status"] == str(status)
    assert "href" not in resp.json.keys()


@pytest.mark.parametrize("status", (REJECTED, REVOKED, FAILURE))
@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_failure(
    client,
    uuid,
    type_,
    status,
    mock_request_task_mapping,
    mock_async_results,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500
    assert resp.json["id"] == uuid
    assert resp.json["status"] == str(status)
    assert "href" not in resp.json.keys()
