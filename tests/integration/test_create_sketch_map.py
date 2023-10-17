from uuid import UUID

import pytest
import requests


@pytest.fixture
def url():
    return "http://localhost:8081/create/results"


@pytest.fixture
def params():
    return {
        "format": "A4",
        "orientation": "landscape",
        "bbox": (
            "[964774.123559138,6343689.928073838,967198.3717426618,6345719.012706632]"
        ),
        "bboxWGS84": (
            "[8.666713409161893,49.40398878092867,8.688490801119476,49.41584842225927]"
        ),
        "size": '{"width": 1716,"height": 1436}',
        "scale": "9051.161965312804",
    }


@pytest.fixture
def uuid(url, params):
    url = "http://localhost:8081/create/results"
    response = requests.post(url, data=params)
    url_parts = response.url.rsplit("/")
    uuid = url_parts[-1]
    return uuid


def test_create_results_post(url, params):
    response = requests.post(url, data=params)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.url.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "http://localhost:8081/create/results"
