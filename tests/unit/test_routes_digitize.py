import io
from uuid import UUID, uuid4

import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def mock_tasks(monkeypatch):
    """Mock celery tasks results."""

    class MockTask:
        id = uuid4()

    mock_task = MockTask()
    monkeypatch.setattr(
        "sketch_map_tool.routes.tasks.generate_digitized_results.apply_async",
        lambda args: mock_task,
    )


def test_digitize(client):
    resp = client.get("/digitize")
    assert resp.status_code == 200



def test_digitize_result_get(client):
    """GET /digitize/results without UUID should redirect to /digitize"""
    resp = client.get("/digitize/results")
    redirect_path = "/digitize"
    assert resp.status_code == 302 and resp.headers.get("Location") == redirect_path


def test_digitize_result_post(client, mock_tasks, monkeypatch):
    """Redirect to /digitize/results/<uuid>"""
    data = {"file": [(io.BytesIO(b"someImageBytes"), "test.jpg")]}
    resp = client.post("/digitize/results", data=data)
    print(resp.headers.get("Location"))
    partial_redirect_path = "/digitize/results"
    location_header = resp.headers.get("Location")
    assert resp.status_code == 302 \
           and location_header is not None \
           and partial_redirect_path in location_header


def test_digitize_result_post_no_files(client, mock_tasks, monkeypatch):
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
