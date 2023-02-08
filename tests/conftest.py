from io import BytesIO
from uuid import uuid4

import cv2
import geojson
import pytest
from werkzeug.datastructures import FileStorage

from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.models import Bbox, PaperFormat, Size
from tests import FIXTURE_DIR

from sketch_map_tool import make_flask

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


# TODO: remove if not used
# @pytest.fixture()
# def db_conn_flask():
#     # setup
#     db_client_flask.open_connection()
#     yield None
#     # teardown
#     db_client_flask.close_connection()


@pytest.fixture()
def db_conn_celery():
    # setup
    db_client_celery.open_connection()
    yield None
    # teardown
    db_client_celery.close_connection()



@pytest.fixture()
def flask_app():
    yield make_flask()


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
        scale_height=0.33,
        qr_y=1.0,
        indent=0.25,
        qr_contents_distances_not_rotated=(2, 3),
        qr_contents_distance_rotated=3,
    )


@pytest.fixture
def scale():
    return 10231.143861780083


@pytest.fixture
def uuid():
    return "654dd0d3-7bb0-4a05-8a68-517f0d9fc98e"


@pytest.fixture
def bbox_as_list():
    return [964472.1973848869, 6343459.035638228, 967434.6098457306, 6345977.635778541]


@pytest.fixture
def bbox_wgs84():
    return Bbox(lon_min=8.625, lat_min=49.3711, lon_max=8.7334, lat_max=49.4397)


@pytest.fixture
def size_as_dict():
    return {"width": 1867, "height": 1587}


@pytest.fixture
def sketch_map_buffer():
    """Photo of a Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map_markings_buffer_1():
    """Photo of a Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map-markings-1.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map_markings_buffer_2():
    """Photo of a Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map-markings-2.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def map_frame_buffer():
    """Map frame of original Sketch Map."""
    with open(str(FIXTURE_DIR / "map-frame.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map_frame_markings_buffer():
    """Map frame of original Sketch Map with detected markings."""
    with open(str(FIXTURE_DIR / "map-frame-markings.geotiff"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def sketch_map_frame_markings_detected_buffer():
    path = str(FIXTURE_DIR / "sketch-map-frame-markings-detected.geotiff")
    with open(path, "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def detected_markings_cleaned_buffer():
    path = str(FIXTURE_DIR / "detected-markings.geojson")
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
def sketch_map_frame_markings():
    return cv2.imread(str(FIXTURE_DIR / "sketch-map-frame-markings.png"))


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


@pytest.fixture()
def file_ids(files, flask_app):
    """IDs of uploaded files stored in the database."""
    with flask_app.app_context():
        # setup
        ids = db_client_flask.insert_files(files)
        yield ids
        # teardown
        for i in ids:
            db_client_flask.delete_file(i)


@pytest.fixture()
def uuids(map_frame_buffer, db_conn_celery):
    """UUIDs of map frames stored in the database."""
    # setup
    uuids = []
    for i in range(3):
        uuid = uuid4()
        uuids.append(uuid)
        db_client_celery.insert_map_frame(map_frame_buffer, uuid)
    yield uuids
    # teardown
    for i in uuids:
        db_client_celery.delete_map_frame(i)
