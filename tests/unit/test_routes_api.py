from unittest.mock import Mock

import pytest
from celery.app.control import Control as CeleryControl
from celery.result import AsyncResult, GroupResult

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def mock_request_task_mapping(uuid, monkeypatch):
    """Mock request id to task id mapping."""
    monkeypatch.setattr(
        "sketch_map_tool.routes.db_client_flask.get_async_result_id",
        lambda *_: uuid,
    )


@pytest.fixture()
def mock_async_result_success(monkeypatch):
    mock = Mock(spec=AsyncResult)
    mock.status = "SUCCESS"
    mock.ready.return_value = True
    mock.failed.return_value = False
    mock.successful.return_value = True

    monkeypatch.setattr("sketch_map_tool.routes.celery_app.AsyncResult", lambda _: mock)
    return mock


@pytest.fixture()
def mock_async_result_started(monkeypatch):
    mock = Mock(spec=AsyncResult)
    mock.status = "STARTED"
    mock.ready.return_value = False
    mock.failed.return_value = False
    mock.successful.return_value = False
    monkeypatch.setattr("sketch_map_tool.routes.celery_app.AsyncResult", lambda _: mock)
    return mock


@pytest.fixture()
def mock_async_result_failure(monkeypatch):
    """Mock task result wich failed w/ expected error"""
    mock = Mock(spec=AsyncResult)
    mock.status = "FAILURE"
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.get.side_effect = QRCodeError("Mock error")
    monkeypatch.setattr("sketch_map_tool.routes.celery_app.AsyncResult", lambda _: mock)
    return mock


@pytest.fixture()
def mock_async_results_failure_hard(monkeypatch):
    """Mock task result wich failed w/ unexpected error"""
    mock = Mock(spec=AsyncResult)
    mock.status = "FAILURE"
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.get.side_effect = ValueError()
    monkeypatch.setattr("sketch_map_tool.routes.celery_app.AsyncResult", lambda _: mock)


@pytest.fixture()
def mock_group_result_success(monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = False
    mock.successful.return_value = True

    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.GroupResult.restore", lambda _: mock
    )


@pytest.fixture
def mock_group_result_started(mock_async_result_started, monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = False
    mock.failed.return_value = False
    mock.successful.return_value = True
    mock.results = [mock_async_result_started]

    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.GroupResult.restore", lambda _: mock
    )


@pytest.fixture
def mock_group_result_failure(mock_async_result_failure, monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [mock_async_result_failure]
    mock.get.side_effect = mock_async_result_failure.get

    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.GroupResult.restore", lambda _: mock
    )


@pytest.fixture
def mock_group_result_started_success_failure(
    mock_async_result_started,
    mock_async_result_success,
    mock_async_result_failure,
    monkeypatch,
):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = False
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [
        mock_async_result_started,
        mock_async_result_success,
        mock_async_result_failure,
    ]
    mock.get.side_effect = mock_async_result_failure.get

    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.GroupResult.restore", lambda _: mock
    )


@pytest.fixture
def mock_celery_control_ping_ok(monkeypatch):
    monkeypatch.setattr(
        CeleryControl,
        "ping",
        lambda *args, **kwargs: [{"workerid": {"ok": "pong"}}],
    )


@pytest.fixture
def mock_celery_control_ping_fail(monkeypatch):
    monkeypatch.setattr(
        CeleryControl,
        "ping",
        lambda *args, **kwargs: [],
    )


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_success(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_result_success,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)
    assert "info" not in resp.json.keys()
    assert "error" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_started(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_result_started,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "STARTED"
    assert resp.json["info"] == {"current": 0, "total": 1}
    assert "href" not in resp.json.keys()
    assert "error" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_failure(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_result_failure,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 422
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "FAILURE"
    assert resp.json["error"] == "QRCodeError: Mock error"
    assert "href" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_failure_hard(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_failure_hard,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "FAILURE"
    assert resp.json["error"] == "ValueError: "
    assert "href" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_success(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_group_result_success,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_started(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_group_result_started,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "STARTED"
    assert resp.json["info"] == {"current": 0, "total": 1}


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_failure(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_group_result_failure,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 422
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "FAILURE"


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_started_success_failure(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_group_result_started_success_failure,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "STARTED"
    assert resp.json["info"] == {"current": 2, "total": 3}


@pytest.mark.usefixtures("mock_celery_control_ping_ok")
def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


@pytest.mark.usefixtures("mock_celery_control_ping_fail")
def test_health_fail(client):
    resp = client.get("/api/health")
    assert resp.status_code == 503
