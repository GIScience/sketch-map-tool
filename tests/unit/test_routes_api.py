import pytest

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def mock_DbConn(uuid, monkeypatch):
    """Mock DbConn context manager."""

    class MockDbConn:
        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_value, exc_tb):
            pass

    monkeypatch.setattr("sketch_map_tool.routes.db_client.DbConn", MockDbConn)


@pytest.fixture()
def mock_request_task_mapping(uuid, monkeypatch):
    """Mock request id to task id mapping."""
    monkeypatch.setattr(
        "sketch_map_tool.routes.db_client.get_async_result_id", lambda uuid, type_: uuid
    )


@pytest.fixture()
def mock_async_results_successful(monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
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


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_successful(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_successful,
    mock_DbConn,
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
    mock_DbConn,
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
    mock_DbConn,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 422
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "FAILED"
    assert resp.json["error"] == "Mock error"
    assert "href" not in resp.json.keys()


@pytest.mark.parametrize("type_", ("sketch-map", "quality-report"))
def test_status_failed_hard(
    client,
    uuid,
    type_,
    mock_request_task_mapping,
    mock_async_results_failed_hard,
    mock_DbConn,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500
