import os.path
from pathlib import Path
from time import sleep
from uuid import UUID

import fitz
import geojson
import pytest
import requests

from tests import vcr_app as vcr

a4 = {
    "format": "A4",
    "orientation": "landscape",
    "bbox": ("[964445.3646475708,6343463.48326091,967408.255014792,6345943.466874749]"),
    "bboxWGS84": (
        "[8.66376011761138,49.40266507327297,8.690376214631833,49.41716014123875]"
    ),
    "size": '{"width": 1716,"height": 1436}',
    "scale": "9051.161965312804",
}

# TODO: Add other params
@pytest.fixture(scope="session", params=[a4])
def params(request):
    return request.param


@pytest.fixture(scope="session")
@vcr.use_cassette
def uuid(params):
    url = "http://localhost:8081/create/results"
    response = requests.post(url, data=params)
    url_parts = response.url.rsplit("/")
    uuid = url_parts[-1]
    return uuid


@pytest.fixture(scope="session")
def sketch_map_pdf(uuid, tmp_path_factory) -> Path:
    fn = tmp_path_factory.mktemp(uuid, numbered=False) / "sketch-map.pdf"
    probe_status_endpoint(uuid, "sketch-map")
    response = requests.get(f"http://localhost:8081/api/download/{uuid}/sketch-map")
    with open(fn, "wb") as file:
        file.write(response.content)
    return fn


def draw_line_on_png(png):
    """Draw a single straight line in the middle of a png"""
    width, height = png.width, png.height
    line_start_x = int(width / 4)
    line_end_x = int(width / 2)
    middle_y = int(height / 2)
    for x in range(line_start_x, line_end_x):
        for y in range(middle_y - 4, middle_y):
            png.set_pixel(x, y, (138, 29, 12))
    return png


@pytest.fixture(scope="session")
def sketch_map_png(sketch_map_pdf, tmp_path_factory, uuid):
    with open(sketch_map_pdf, "rb") as file:
        sketch_map_pdf = file.read()
    pdf = fitz.open(stream=sketch_map_pdf)
    page = pdf.load_page(0)
    png = page.get_pixmap()

    png = draw_line_on_png(png)

    path = tmp_path_factory.getbasetemp() / uuid / "sketch-map.png"
    png.save(path, output="png")
    return path


@pytest.fixture(scope="session")
def uuid_result_uploaded(sketch_map_png):
    url = "http://localhost:8081/digitize/results"
    with open(sketch_map_png, "rb") as file:
        files = {"file": file}
        response = requests.post(url, files=files)
    response.raise_for_status()

    # Extract UUID from response
    url_parts = response.url.rsplit("/")
    uuid = url_parts[-1]
    return uuid


def test_sketch_map_pdf(sketch_map_pdf):
    # test if fixture is created successfully
    with open(sketch_map_pdf, "rb") as file:
        sketch_map_pdf = file.read()
    assert sketch_map_pdf is not None
    assert len(sketch_map_pdf) > 0


def test_sketch_map_png(sketch_map_png):
    # test if fixture is created successfully
    with open(sketch_map_png, "rb") as file:
        sketch_map_png = file.read()
    assert sketch_map_png is not None
    assert len(sketch_map_png) > 0


@vcr.use_cassette
def test_create_results_post(params):
    url = "http://localhost:8081/create/results"
    response = requests.post(url, data=params)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.url.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "http://localhost:8081/create/results"


def test_api_status_uuid_sketch_map(uuid):
    # for 30 seconds check status
    probe_status_endpoint(uuid, "sketch-map")


def test_api_download_uuid_sketch_map(uuid):
    # for 30 seconds check status
    probe_status_endpoint(uuid, "sketch-map")

    response = requests.get(f"http://localhost:8081/api/download/{uuid}/sketch-map")
    assert response.status_code == 200
    assert len(response.content) > 0


def test_digitize_results_post(sketch_map_png):
    url = "http://localhost:8081/digitize/results"
    with open(sketch_map_png, "rb") as file:
        files = {"file": file}
        response = requests.post(url, files=files)
    assert response.status_code == 200

    # Extract UUID from response
    url_parts = response.url.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])

    assert UUID(uuid).version == 4
    assert url_rest == "http://localhost:8081/digitize/results"


def probe_status_endpoint(uuid, endpoint):
    """Wait for computations to be finished and status to return 200 or fail."""
    # for 30 seconds check status
    for _ in range(30):
        response = requests.get(f"http://localhost:8081/api/status/{uuid}/{endpoint}")
        assert response.status_code in (200, 202)
        result = response.json()

        status = result.pop("status")
        assert status in ("SUCCESS", "PENDING", "RETRY", "STARTED")

        href = result.pop("href", None)
        assert result == {"id": uuid, "type": endpoint}

        if response.status_code == 200:
            assert href == "/api/download/" + uuid + f"/{endpoint}"
            assert status == "SUCCESS"
            break
        sleep(1)
    assert response.status_code == 200, "Status not 200 after 30 seconds"


def test_api_status_uuid_raster_and_vector_results(uuid_result_uploaded):
    probe_status_endpoint(uuid_result_uploaded, "raster-results")
    probe_status_endpoint(uuid_result_uploaded, "vector-results")


def test_api_download_uuid_vector_result(uuid_result_uploaded):
    probe_status_endpoint(uuid_result_uploaded, "vector-results")

    response = requests.get(
        f"http://localhost:8081/api/download/{uuid_result_uploaded}/vector-results"
    )

    assert response.status_code == 200
    json = geojson.loads(geojson.dumps(response.json()))
    assert len(json["features"]) > 0
    assert json.is_valid


def test_api_download_uuid_raster_result(uuid_result_uploaded):
    probe_status_endpoint(uuid_result_uploaded, "raster-results")

    response = requests.get(
        f"http://localhost:8081/api/download/{uuid_result_uploaded}/raster-results"
    )
    assert response.status_code == 200
    assert len(response.content) > 0


@pytest.fixture
def vector_result(uuid_result_uploaded, tmp_path_factory):
    probe_status_endpoint(uuid_result_uploaded, "vector-results")

    response = requests.get(
        f"http://localhost:8081/api/download/{uuid_result_uploaded}/vector-results"
    )
    response.raise_for_status()

    # check if folder exists
    if not os.path.exists(tmp_path_factory.getbasetemp() / uuid_result_uploaded):
        fn = (
            tmp_path_factory.mktemp(uuid_result_uploaded, numbered=False)
            / "vector-results.geojson"
        )
    else:
        fn = (
            tmp_path_factory.getbasetemp()
            / uuid_result_uploaded
            / "vector-results.geojson"
        )
    with open(fn, "w") as file:
        geojson.dump(response.json(), file)
    return fn


@pytest.fixture
def raster_result(uuid_result_uploaded, tmp_path_factory):
    probe_status_endpoint(uuid_result_uploaded, "raster-results")

    response = requests.get(
        f"http://localhost:8081/api/download/{uuid_result_uploaded}/raster-results"
    )
    response.raise_for_status()

    # check if folder exists
    if not os.path.exists(tmp_path_factory.getbasetemp() / uuid_result_uploaded):
        fn = (
            tmp_path_factory.mktemp(uuid_result_uploaded, numbered=False)
            / "raster-results.zip"
        )
    else:
        fn = (
            tmp_path_factory.getbasetemp() / uuid_result_uploaded / "raster-results.zip"
        )
    with open(fn, "wb") as file:
        file.write(response.content)
    return fn


def test_vector_and_raster_fixtures(vector_result, raster_result):
    assert vector_result.exists()
    assert raster_result.exists()
