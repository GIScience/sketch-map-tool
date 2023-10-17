from pathlib import Path
from time import sleep
from uuid import UUID

import fitz
import pytest
import requests

from tests import vcr_app as vcr


@pytest.fixture(scope="session")
def params():
    return {
        "format": "A4",
        "orientation": "landscape",
        "bbox": (
            "[964445.3646475708,6343463.48326091,967408.255014792,6345943.466874749]"
        ),
        "bboxWGS84": (
            "[8.66376011761138,49.40266507327297,8.690376214631833,49.41716014123875]"
        ),
        "size": '{"width": 1716,"height": 1436}',
        "scale": "9051.161965312804",
    }


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
    # for 20 seconds check status
    # TODO: decide on time to wait
    for _ in range(20):
        response = requests.get(f"http://localhost:8081/api/status/{uuid}/sketch-map")
        if response.status_code == 200:
            response = requests.get(
                f"http://localhost:8081/api/download/{uuid}/sketch-map"
            )
            with open(fn, "wb") as file:
                file.write(response.content)
            return fn
        sleep(1)
    raise TimeoutError("Sketch map PDF not created")


@pytest.fixture
def sketch_map_png(sketch_map_pdf, tmp_path_factory, uuid):
    with open(sketch_map_pdf, "rb") as file:
        sketch_map_pdf = file.read()
    pdf = fitz.open(stream=sketch_map_pdf)
    page = pdf.load_page(0)
    png = page.get_pixmap()
    path = tmp_path_factory.getbasetemp() / uuid / "sketch-map.png"
    png.save(path, output="png")
    return path


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
    # for 20 seconds check status
    # TODO: decide on time to wait
    for _ in range(20):
        response = requests.get(f"http://localhost:8081/api/status/{uuid}/sketch-map")
        assert response.status_code in (200, 202)
        if response.status_code == 200:
            break
        sleep(1)
    assert response.status_code == 200


def test_api_download_uuid_sketch_map(uuid):
    # for 20 seconds check status
    # TODO: decide on time to wait
    for _ in range(20):
        response = requests.get(f"http://localhost:8081/api/status/{uuid}/sketch-map")
        if response.status_code == 200:
            response = requests.get(
                f"http://localhost:8081/api/download/{uuid}/sketch-map"
            )
            break
        sleep(1)
    assert response.status_code == 200


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


def test_sketch_map_pdf(sketch_map_pdf):
    # test fixture is created successfully
    with open(sketch_map_pdf, "rb") as file:
        sketch_map_pdf = file.read()
    assert sketch_map_pdf is not None
    assert len(sketch_map_pdf) > 0


def test_sketch_map_png(sketch_map_png):
    # test fixture is created successfully
    with open(sketch_map_png, "rb") as file:
        sketch_map_png = file.read()
    assert sketch_map_png is not None
    assert len(sketch_map_png) > 0
