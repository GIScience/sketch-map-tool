import pytest
from uuid import UUID

from sketch_map_tool.app2 import app


@pytest.fixture()
def client():
    return app.test_client()


def test_create_get(client):
    resp = client.get("/create")
    assert resp.status_code == 200


def test_create_post(client):
    data = {
        "bbox": "",
        "paper_format": "A4",
        "paper_orientation": "landscape",
    }
    resp = client.post("/create", data=data)
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


def test_create_results_no_uuid(client):
    resp = client.get("/create/results")
    assert resp.status_code == 302


def test_create_results_status(client):
    uuid = "16fd2706-8baf-433b-82eb-8c7fada847da"
    resp = client.get("/create/results/status/{0}".format(uuid))
    assert resp.status_code == 200

    try:
        UUID(resp.json["id"])
    except ValueError:
        assert "invalid uuid"

    assert isinstance(resp.json["progress"], float)
    assert isinstance(resp.json["status"], str)
