from io import BytesIO
from uuid import UUID, uuid4

import pytest

from sketch_map_tool import flask_app as app
from sketch_map_tool.database import client_flask


@pytest.fixture
def map_frame_legacy_2024_04_15(flask_app, uuid_create, map_frame):
    """Legacy map frames in DB do not have bbox, lon, lat and format set."""
    with flask_app.app_context():
        select_query = """
        SELECT bbox, lat, lon, format, orientation, layer, version
        FROM map_frame WHERE uuid = %s
        """
        update_query = """
        UPDATE map_frame SET bbox = NULL, lat = NULL, lon = NULL, format = NULL,
            orientation = NULL, layer = NULL, version = NULL
        WHERE uuid = %s
        """
        with client_flask.open_connection().cursor() as curs:
            curs.execute(select_query, [uuid_create])
            vals = curs.fetchone()
            curs.execute(update_query, [uuid_create])

    yield map_frame

    map_frame.seek(0)
    with flask_app.app_context():
        update_query = """
        UPDATE map_frame
        SET bbox = %s, lat = %s, lon = %s, format = %s,
            orientation = %s, layer = %s, version = %s
        WHERE uuid = %s
        """
        with client_flask.open_connection().cursor() as curs:
            curs.execute(update_query, vals + tuple([uuid_create]))


def get_consent_flag_from_db(file_name: str) -> bool:
    query = "SELECT consent FROM blob WHERE file_name = %s"
    db_conn = client_flask.open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [file_name])
        return curs.fetchone()[0]


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
    unique_file_name = str(uuid4())
    data = {"file": [(BytesIO(sketch_map_marked), unique_file_name)], "consent": "True"}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"
    with app.app_context():
        assert get_consent_flag_from_db(unique_file_name) is True


def test_digitize_results_post_no_consent(sketch_map_marked, flask_client):
    # do not send consent parameter
    # -> consent is a checkbox and only send if selected
    unique_file_name = str(uuid4())
    data = {"file": [(BytesIO(sketch_map_marked), unique_file_name)]}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"
    with app.app_context():
        assert get_consent_flag_from_db(unique_file_name) is False


def test_digitize_results_legacy_2024_04_15(
    sketch_map_marked,
    map_frame_legacy_2024_04_15,
    flask_client,
):
    """Legacy map frames in DB do not have bbox, lon, lat and format set."""
    unique_file_name = str(uuid4())
    data = {"file": [(BytesIO(sketch_map_marked), unique_file_name)], "consent": "True"}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"
    with app.app_context():
        assert get_consent_flag_from_db(unique_file_name) is True


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
