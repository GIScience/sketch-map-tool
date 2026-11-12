import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


def test_index(client, monkeypatch: pytest.MonkeyPatch):
    def status(*args, **kwargs):
        raise Exception

    monkeypatch.setattr("sketch_map_tool.routes.status", status)
    resp = client.get("/api/status")
    assert resp.status_code == 500
    assert "msg" in resp.json.keys()
