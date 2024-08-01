import pytest
from celery.app.control import Control as CeleryControl

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
        lambda uuid, type_: uuid,
    )


@pytest.fixture()
def mock_async_results_successful(monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        status = "SUCCESSFUL"

        def get(*args, **kwargs):
            pass

        def ready(self):
            return True

        def failed(self):
            return False

        def successful(self):
            return True

    mock_task = MockTask()
    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.AsyncResult",
        lambda x: mock_task,
    )


@pytest.fixture()
def mock_async_results_processing(monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        status = "PROCESSING"

        def get(*args, **kwargs):
            pass

        def ready(self):
            return False

    mock_task = MockTask()
    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.AsyncResult",
        lambda x: mock_task,
    )


@pytest.fixture()
def mock_async_results_failed(request, monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        status = "FAILED"

        def get(*args, **kwargs):
            raise QRCodeError("Mock error")

        def ready(self):
            return True

        def failed(self):
            return True

        def successful(self):
            return False

    mock_task = MockTask()
    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.AsyncResult",
        lambda x: mock_task,
    )


@pytest.fixture()
def mock_async_results_failed_hard(request, monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        status = "FAILED"

        def get(*args, **kwargs):
            raise ValueError()
            pass

        def ready(self):
            return True

        def failed(self):
            return True

        def successful(self):
            return False

    mock_task = MockTask()
    monkeypatch.setattr(
        "sketch_map_tool.routes.celery_app.AsyncResult",
        lambda x: mock_task,
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
def test_status_successful(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_successful,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "SUCCESSFUL"
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_processing(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_processing,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "PROCESSING"
    assert "href" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_failed(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_failed,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 422
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "FAILED"
    assert resp.json["error"] == "QRCodeError: Mock error"
    assert "href" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_failed_hard(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_failed_hard,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500


@pytest.mark.usefixtures("mock_celery_control_ping_ok")
def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


@pytest.mark.usefixtures("mock_celery_control_ping_fail")
def test_health_fail(client):
    resp = client.get("/api/health")
    assert resp.status_code == 503
