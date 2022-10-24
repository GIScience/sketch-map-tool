from uuid import UUID

import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


def test_create(client):
    resp = client.get("/create")
    assert resp.status_code == 200


def test_create_result_get(client):
    resp = client.get("/create/results")
    assert resp.status_code == 302  # Redirect


def test_create_result_post(client):
    data = {
        "bbox": "[965172.1534546925,6343953.965425534,966970.2550592694,6345482.705991237]",
        "format": "A4",
        "orientation": "landscape",
        "size": "{\"width\":1867,\"height\":1587}"
    }
    resp = client.post("/create/results", data=data)
    assert resp.status_code == 200


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
