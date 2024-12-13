import pytest
from celery.app.control import Control as CeleryControl


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


@pytest.mark.usefixtures("mock_celery_control_ping_ok")
def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


@pytest.mark.usefixtures("mock_celery_control_ping_fail")
def test_health_fail(client):
    resp = client.get("/api/health")
    assert resp.status_code == 503
