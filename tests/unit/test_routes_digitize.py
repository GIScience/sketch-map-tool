import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def mock_task(uuid, monkeypatch):
    """Mock celery workflow generate digitized results."""
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.t_digitize_sketches", lambda args: uuid
    )
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.t_georeference_sketch_maps", lambda args: uuid
    )


def test_digitize(client):
    resp = client.get("/digitize")
    assert resp.status_code == 200


def test_digitize_result_get(client):
    """GET /digitize/results without UUID should redirect to /digitize"""
    resp = client.get("/digitize/results")
    redirect_path = "/digitize"
    assert resp.status_code == 302 and resp.headers.get("Location") == redirect_path


@pytest.mark.skip(reason="Mocking of chained/grouped tasks is too complex for now")
def test_digitize_result_post(client, sketch_map_buffer, mock_task):
    """Redirect to /digitize/results/<uuid>"""
    data = {"file": [(sketch_map_buffer, "sketch_map.png")]}
    resp = client.post("/digitize/results", data=data)
    print(resp.headers.get("Location"))
    partial_redirect_path = "/digitize/results"
    location_header = resp.headers.get("Location")
    assert (
        resp.status_code == 302
        and location_header is not None
        and partial_redirect_path in location_header
    )


def test_digitize_result_post_no_files(client, mock_task):
    """Redirect to upload form to stay on the same page and try again"""
    data = {}
    resp = client.post("/digitize/results", data=data)
    redirect_path = "/digitize"
    assert resp.status_code == 302 and resp.headers.get("Location") == redirect_path


def test_digitize_results_uuid(client):
    """Deliver the website if a valid uuid is passed"""
    uuid = "16fd2706-8baf-433b-82eb-8c7fada847da"
    resp = client.get("/digitize/results/{0}".format(uuid))
    assert resp.status_code == 200


def test_digitize_results_uuid_not_found(client):
    """A valid UUID format should still be evaluated for existence in the result store"""
    uuid = "16fd2706-8baf-433b-82eb-8c7fada847db"
    resp = client.get("/digitize/results/{0}".format(uuid))
    assert resp.status_code == 200
    # TODO: Should be 404
    # assert resp.status_code == 404


def test_digitize_results_invalid_uuid(client):
    """A wrong uuid format should result in an error"""
    uuid = "foo"
    resp = client.get("/digitize/results/{0}".format(uuid))
    assert resp.status_code == 500
