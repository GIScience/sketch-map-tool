from uuid import UUID

import pytest

from sketch_map_tool.routes import app


@pytest.fixture()
def client():
    return app.test_client()


def test_create_results_status(client):
    uuid = "16fd2706-8baf-433b-82eb-8c7fada847da"
    resp = client.get("/api/status/{0}".format(uuid))
    assert resp.status_code == 200

    try:
        UUID(resp.json["id"])
    except ValueError:
        assert "invalid uuid"

    assert isinstance(resp.json["status"], str)
