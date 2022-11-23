import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_help(client):
    resp = client.get("/help")
    assert resp.status_code == 200


def test_about(client):
    resp = client.get("/about")
    assert resp.status_code == 200
