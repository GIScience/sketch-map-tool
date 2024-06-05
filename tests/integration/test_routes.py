from io import BytesIO
from uuid import UUID

import pytest

from sketch_map_tool import flask_app as app
from sketch_map_tool.database.client_flask import open_connection


def test_create_results_post(params, flask_client):
    response = flask_client.post("/create/results", data=params, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/create/results"


def test_digitize_results_post(sketch_map_marked, flask_client):
    data = {"file": [(BytesIO(sketch_map_marked), "sketch_map.png")], "consent": "True"}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"


def test_digitize_results_post_no_consent(sketch_map_marked, flask_client):
    # do not send consent parameter
    # -> consent is a checkbox and only send if selected
    data = {"file": [(BytesIO(sketch_map_marked), "sketch_map.png")]}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"
    with app.app_context():
        raw = select_file(1)
        assert raw is False

    # TODO: check consent flag in database


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


def test_health_ok(flask_client):
    resp = flask_client.get("/api/health")
    assert resp.status_code == 200


def select_file(id_: int) -> bytes:
    """Get an uploaded file stored in the database by ID."""
    query = "SELECT * FROM blob WHERE id = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            return raw[3]
