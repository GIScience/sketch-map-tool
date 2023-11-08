from io import BytesIO
from uuid import uuid4

import pytest
from celery.contrib.testing.tasks import ping  # noqa: F401
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from werkzeug.datastructures import FileStorage

from sketch_map_tool import CELERY_CONFIG, make_flask
from sketch_map_tool import celery_app as smt_celery_app
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.routes import (
    about,
    digitize,
    digitize_results_post,
    help,
    index,
)
from tests import FIXTURE_DIR


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="session", autouse=True)
def postgres_container(monkeypatch_session):
    """Spin up a Postgres container available for all tests.

    Connection string will be different for each test session.
    """
    with PostgresContainer("postgres:15") as postgres:
        conn = "db+postgresql://{user}:{password}@127.0.0.1:{port}/{database}".format(
            user=postgres.POSTGRES_USER,
            password=postgres.POSTGRES_PASSWORD,
            port=postgres.get_exposed_port(5432),  # 5432 is default port of postgres
            database=postgres.POSTGRES_DB,
        )
        monkeypatch_session.setenv("SMT-RESULT-BACKEND", conn)
        yield {"connection_url": conn}
    # cleanup


@pytest.fixture(scope="session", autouse=True)
def redis_container(monkeypatch_session):
    """Spin up a Redis container available for all tests.

    Connection string will be different for each test session.
    """
    with RedisContainer("redis:7") as redis:
        port = redis.get_exposed_port(6379)  # 6379 is default port of redis
        conn = f"redis://127.0.0.1:{port}"
        monkeypatch_session.setenv("SMT-BROKER-URL", conn)
        yield {"connection_url": conn}
    # cleanup


@pytest.fixture(scope="session", autouse=True)
def celery_config(postgres_container, redis_container):
    """Set Celery config to point at testcontainers."""
    CELERY_CONFIG["result_backend"] = postgres_container["connection_url"]
    CELERY_CONFIG["broker_url"] = redis_container["connection_url"]
    return CELERY_CONFIG


@pytest.fixture(scope="session", autouse=True)
def celery_app(celery_config):
    """Configure Celery test app."""
    smt_celery_app.conf.update(celery_config)
    return smt_celery_app


@pytest.fixture(autouse=True)
def celery_worker(celery_worker):
    return celery_worker


@pytest.fixture()
def flask_app():
    app = make_flask()
    app.config.update(
        {
            "TESTING": True,
        }
    )
    # Register routes to be tested:
    app.add_url_rule(
        "/digitize/results",
        view_func=digitize_results_post,
        methods=["POST", "GET"],
    )
    app.add_url_rule("/digitize", view_func=digitize, methods=["GET"])
    app.add_url_rule("/", view_func=index, methods=["GET"])
    app.add_url_rule("/about", view_func=about, methods=["GET"])
    app.add_url_rule("/help", view_func=help, methods=["GET"])
    yield app


@pytest.fixture()
def flask_client(flask_app):
    return flask_app.test_client()


@pytest.fixture()
def db_conn_celery():
    # setup
    db_client_celery.open_connection()
    yield None
    # teardown
    db_client_celery.close_connection()


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


@pytest.fixture
def uuid():
    return "654dd0d3-7bb0-4a05-8a68-517f0d9fc98e"


@pytest.fixture
def bbox_wgs84():
    return Bbox(lon_min=8.625, lat_min=49.3711, lon_max=8.7334, lat_max=49.4397)


@pytest.fixture
def sketch_map_buffer():
    """Photo of a Sketch Map."""
    with open(str(FIXTURE_DIR / "sketch-map.png"), "rb") as file:
        return BytesIO(file.read())


@pytest.fixture
def map_frame_buffer():
    """Map frame of original Sketch Map."""
    with open(str(FIXTURE_DIR / "map-frame.png"), "rb") as file:
        return BytesIO(file.read())


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
