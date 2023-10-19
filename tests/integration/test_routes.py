from io import BytesIO
from uuid import UUID

import pytest


def test_create_results_post(params, flask_client):
    response = flask_client.post("/create/results", data=params, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/create/results"


def test_digitize_results_post(sketch_map_png, flask_client):
    data = {"file": [(BytesIO(sketch_map_png), "sketch_map.png")]}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"


def test_api_status_uuid_sketch_map(uuid_create, flask_client):
    resp = flask_client.get(f"/api/status/{uuid_create}/sketch-map")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid_create
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == f"/api/download/{uuid_create}/sketch-map"


@pytest.mark.parametrize(
    "type_",
    ["vector-results", "raster-results"],
)
def test_api_status_uuid_digitize(uuid_digitize, type_, flask_client):
    resp = flask_client.get(f"/api/status/{uuid_digitize}/{type_}")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid_digitize
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == f"/api/download/{uuid_digitize}/{type_}"


def test_api_download_uuid_sketch_map(uuid_create, flask_client):
    resp = flask_client.get(f"/api/download/{uuid_create}/sketch-map")
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "type_",
    ["vector-results", "raster-results"],
)
def test_api_download_uuid_digitize(uuid_digitize, type_, flask_client):
    resp = flask_client.get(f"/api/download/{uuid_digitize}/{type_}")
    assert resp.status_code == 200
