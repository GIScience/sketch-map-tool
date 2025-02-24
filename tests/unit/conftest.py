from io import BytesIO
from unittest.mock import Mock

import cv2
import geojson
import pytest
from celery.result import AsyncResult, GroupResult
from werkzeug.datastructures import FileStorage

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.models import Bbox, Layer, PaperFormat, Size
from sketch_map_tool.routes import app
from tests import FIXTURE_DIR


def pytest_addoption(parser):
    parser.addoption(
        "--save-maps",
        action="store_true",
        help="save created maps in parametrized test",
        default=False,
    )
    parser.addoption(
        "--save-report",
        action="store_true",
        help="save created reports in parametrized test",
        default=False,
    )


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture
def bbox():
    return Bbox(
        lon_min=964472.1973848869,
        lat_min=6343459.035638228,
        lon_max=967434.6098457306,
        lat_max=6345977.635778541,
    )


@pytest.fixture
def size():
    return Size(width=1867, height=1587)


@pytest.fixture
def format_():
    return PaperFormat(
        "a4",
        width=29.7,
        height=21,
        right_margin=5,
        map_margin=1.0,
        font_size=8,
        qr_scale=0.6,
        compass_scale=0.25,
        globe_scale=0.125,
        scale_height=1,
        scale_relative_xy=(-15, -30),
        scale_background_params=(-15, -30, 30, 60),
        scale_distance_to_text=20,
        qr_y=1.0,
        indent=0.25,
        qr_contents_distances_not_rotated=(2, 3),
        qr_contents_distance_rotated=3,
    )


@pytest.fixture
def scale():
    return 10231.143861780083


@pytest.fixture(params=["osm", "esri-world-imagery"])
def layer(request):
    return Layer(request.param)


@pytest.fixture(params=[True, False])
def aruco(request):
    return request.param


@pytest.fixture
def uuid():
    return "654dd0d3-7bb0-4a05-8a68-517f0d9fc98e"


@pytest.fixture
def version_nr():
    return "0.9.0"


@pytest.fixture
def bbox_as_list():
    return [964472.1973848869, 6343459.035638228, 967434.6098457306, 6345977.635778541]


@pytest.fixture
def bbox_wgs84():
    return Bbox(lon_min=8.625, lat_min=49.3711, lon_max=8.7334, lat_max=49.4397)


@pytest.fixture
def bbox_wgs84_str():
    return "8.625,49.3711,8.7334,49.4397"


@pytest.fixture
def size_as_dict():
    return {"width": 1867, "height": 1587}


@pytest.fixture
def sketch_map_buffer():
    """Photo of a Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map_frame_markings_detected_buffer():
    path = str(FIXTURE_DIR / "sketch-map-frame-markings-detected.geotiff")
    with open(path, "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map():
    """Photo of a Sketch Map."""
    return cv2.imread(
        str(FIXTURE_DIR / "sketch-map.png"), cv2.IMREAD_COLOR
    )  # BGR color format and no alpha channel


@pytest.fixture
def map_frame():
    """Map frame of original Sketch Map."""
    return cv2.imread(str(FIXTURE_DIR / "map-frame.png"))


@pytest.fixture
def sketch_map_frame_markings_detected():
    return cv2.imread(str(FIXTURE_DIR / "sketch-map-frame-markings-detected.png"))


@pytest.fixture
def detected_markings():
    with open(str(FIXTURE_DIR / "detected-markings.geojson"), "r") as file:
        return geojson.load(file)


@pytest.fixture
def detected_markings_cleaned():
    with open(str(FIXTURE_DIR / "detected-markings-cleaned.geojson"), "r") as file:
        return geojson.load(file)


@pytest.fixture
def file(sketch_map_buffer):
    return FileStorage(stream=sketch_map_buffer, filename="filename")


@pytest.fixture
def files(file):
    return [file, file]


@pytest.fixture(autouse=True)
def mock_request_download_update_map_frame_downloaded(monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.db_client_flask.update_map_frame_downloaded",
        lambda *_: None,
    )


@pytest.fixture(autouse=True)
def mock_request_download_update_files_download_raster(monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.db_client_flask.update_files_download_raster",
        lambda *_: None,
    )


@pytest.fixture(autouse=True)
def mock_request_download_update_files_download_vector(monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.db_client_flask.update_files_download_vector",
        lambda *_: None,
    )


@pytest.fixture()
def mock_async_result_success(monkeypatch):
    mock = Mock(spec=AsyncResult)
    mock.status = "SUCCESS"
    mock.ready.return_value = True
    mock.failed.return_value = False
    mock.successful.return_value = True
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
    return mock


@pytest.fixture()
def mock_async_result_started(monkeypatch):
    mock = Mock(spec=AsyncResult)
    mock.status = "STARTED"
    mock.ready.return_value = False
    mock.failed.return_value = False
    mock.successful.return_value = False
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
    return mock


@pytest.fixture
def mock_async_result_failure(monkeypatch):
    """Mock task result wich failed w/ expected error"""
    mock = Mock(spec=AsyncResult)
    mock.status = "FAILURE"
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.get.side_effect = QRCodeError("Mock error")
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
    return mock


@pytest.fixture
def mock_async_result_failure_hard(monkeypatch):
    """Mock task result wich failed w/ unexpected error"""
    mock = Mock(spec=AsyncResult)
    mock.status = "FAILURE"
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.get.side_effect = ValueError()
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
    return mock


@pytest.fixture
def mock_group_result_success(mock_async_result_success, monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = False
    mock.successful.return_value = True
    mock.get.return_value = [[Mock()]]
    mock.results = [mock_async_result_success]
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
    return mock


@pytest.fixture
def mock_group_result_started(mock_async_result_started, monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = False
    mock.failed.return_value = False
    mock.successful.return_value = True
    mock.results = [mock_async_result_started]
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
    return mock


@pytest.fixture
def mock_group_result_failure(mock_async_result_failure, monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [mock_async_result_failure]
    mock.get.side_effect = mock_async_result_failure.get
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)


@pytest.fixture
def mock_group_result_failure_hard(mock_async_result_failure_hard, monkeypatch):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [mock_async_result_failure_hard]
    mock.get.side_effect = mock_async_result_failure_hard.get
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)


@pytest.fixture
def mock_group_result_started_success_failure(
    mock_async_result_started,
    mock_async_result_success,
    mock_async_result_failure,
    monkeypatch,
):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = False
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [
        mock_async_result_started,
        mock_async_result_success,
        mock_async_result_failure,
    ]
    mock.get.side_effect = mock_async_result_failure.get
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)


@pytest.fixture
def mock_group_result_success_failure(
    mock_async_result_success,
    mock_async_result_failure,
    monkeypatch,
):
    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [
        mock_async_result_success,
        mock_async_result_failure,
    ]
    mock.get.side_effect = mock_async_result_failure.get
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)
