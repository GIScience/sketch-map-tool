import json
from io import BytesIO
from uuid import UUID, uuid4

import fitz
import pytest
from celery.contrib.testing.tasks import ping  # noqa: F401
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from werkzeug.datastructures import FileStorage

from sketch_map_tool import CELERY_CONFIG, make_flask, routes
from sketch_map_tool import celery_app as smt_celery_app
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.models import Bbox, PaperFormat, Size
from tests import FIXTURE_DIR


#
# Session wide test setup of DB (redis and postgres) and workers (flask and celery)
#
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
        monkeypatch_session.setenv("SMT_RESULT_BACKEND", conn)
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
        monkeypatch_session.setenv("SMT_BROKER_URL", conn)
        yield {"connection_url": conn}
    # cleanup


@pytest.fixture(scope="session", autouse=True)
def celery_config(postgres_container, redis_container):
    """Set Celery config to point at testcontainers."""
    CELERY_CONFIG["result_backend"] = postgres_container["connection_url"]
    CELERY_CONFIG["broker_url"] = redis_container["connection_url"]
    return CELERY_CONFIG


@pytest.fixture(scope="session", autouse=True)
def celery_worker_parameters():
    return {"shutdown_timeout": 20}


@pytest.mark.usefixtures("postgres_container", "redis_container")
@pytest.fixture(scope="session", autouse=True)
def celery_app(celery_config):
    """Configure Celery test app."""
    smt_celery_app.conf.update(celery_config)
    return smt_celery_app


@pytest.mark.usefixtures("postgres_container", "redis_container")
@pytest.fixture(scope="session", autouse=True)
def celery_worker(celery_session_worker):
    return celery_session_worker
    # yield celery_session_worker
    # celery_session_worker.terminate()


@pytest.fixture(scope="session")
def flask_app():
    app = make_flask()
    app.config.update(
        {
            "TESTING": True,
        }
    )
    # Register routes to be tested:
    app.add_url_rule(
        "/create/results",
        view_func=routes.create_results_post,
        methods=["POST"],
    )
    app.add_url_rule(
        "/create/results",
        view_func=routes.create_results_get,
        methods=["GET"],
    )
    app.add_url_rule(
        "/create/results/<uuid>",
        view_func=routes.create_results_get,
        methods=["GET"],
    )
    app.add_url_rule(
        "/digitize/results",
        view_func=routes.digitize_results_post,
        methods=["POST"],
    )
    app.add_url_rule(
        "/digitize/results",
        view_func=routes.digitize_results_get,
        methods=["get"],
    )
    app.add_url_rule(
        "/digitize/results/<uuid>",
        view_func=routes.digitize_results_get,
        methods=["get"],
    )
    app.add_url_rule(
        "/api/status/<uuid>/<type_>",
        view_func=routes.status,
        methods=["get"],
    )
    app.add_url_rule(
        "/api/download/<uuid>/<type_>",
        view_func=routes.download,
        methods=["get"],
    )
    app.add_url_rule("/create", view_func=routes.create, methods=["GET"])
    app.add_url_rule("/digitize", view_func=routes.digitize, methods=["GET"])
    app.add_url_rule("/", view_func=routes.index, methods=["GET"])
    app.add_url_rule("/about", view_func=routes.about, methods=["GET"])
    app.add_url_rule("/help", view_func=routes.help, methods=["GET"])
    yield app


@pytest.fixture(scope="session")
def flask_client(flask_app):
    return flask_app.test_client()


@pytest.fixture()
def db_conn_celery():
    # setup
    db_client_celery.open_connection()
    yield None
    # teardown
    db_client_celery.close_connection()


#
# Test input
#
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
def uuid_create(
    params,
    flask_client,
    flask_app,
    celery_app,
    tmp_path_factory,
) -> str:
    response = flask_client.post("/create/results", data=params, follow_redirects=True)

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/create/results"

    # Wait for task to be finished and retrieve result (the sketch map)
    with flask_app.app_context():
        id_ = db_client_flask.get_async_result_id(uuid, "sketch-map")
    task = celery_app.AsyncResult(id_)
    result = task.get(timeout=90)

    # Write sketch map to temporary test directory
    fn = tmp_path_factory.mktemp(uuid, numbered=False) / "sketch-map.pdf"
    with open(fn, "wb") as file:
        file.write(result.getbuffer())

    return uuid


@pytest.fixture(scope="session")
def sketch_map_pdf(uuid_create, tmp_path_factory) -> bytes:
    path = tmp_path_factory.getbasetemp() / uuid_create / "sketch-map.pdf"
    with open(path, "rb") as file:
        return file.read()


@pytest.fixture(scope="session")
def sketch_map_png(uuid_create, sketch_map_pdf, tmp_path_factory) -> BytesIO:
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

    pdf = fitz.open(stream=sketch_map_pdf)
    page = pdf.load_page(0)
    png = page.get_pixmap()
    png = draw_line_on_png(png)  # mock sketches on map
    BytesIO()
    path = tmp_path_factory.getbasetemp() / uuid_create / "sketch-map.png"
    png.save(path, output="png")
    with open(path, "rb") as file:
        return file.read()


@pytest.fixture(scope="session")
def uuid_digitize(
    sketch_map_png,
    flask_client,
    flask_app,
    celery_app,
    tmp_path_factory,
) -> str:
    data = {"file": [(BytesIO(sketch_map_png), "sketch_map.png")]}
    response = flask_client.post("/digitize/results", data=data, follow_redirects=True)

    # Extract UUID from response
    url_parts = response.request.path.rsplit("/")
    uuid = url_parts[-1]
    url_rest = "/".join(url_parts[:-1])
    assert UUID(uuid).version == 4
    assert url_rest == "/digitize/results"

    # Wait for tasks to be finished and retrieve results (vector and raster)
    with flask_app.app_context():
        id_vector = db_client_flask.get_async_result_id(uuid, "vector-results")
        id_raster = db_client_flask.get_async_result_id(uuid, "raster-results")
    task_vector = celery_app.AsyncResult(id_vector)
    task_raster = celery_app.AsyncResult(id_raster)
    result_vector = task_vector.get(timeout=90)
    result_raster = task_raster.get(timeout=90)
    # Write sketch map to temporary test directory
    dir = tmp_path_factory.mktemp(uuid, numbered=False)
    path_vector = dir / "vector.geojson"
    path_raster = dir / "raster.zip"
    with open(path_vector, "w") as file:
        file.write(json.dumps(result_vector))
    with open(path_raster, "wb") as file:
        file.write(result_raster.getbuffer())
    return uuid


@pytest.fixture(scope="session")
def vector(uuid_digitize, tmp_path_factory) -> bytes:
    path = tmp_path_factory.getbasetemp() / uuid_digitize / "vector.geojson"
    with open(path, "rb") as file:
        return file.read()


@pytest.fixture(scope="session")
def raster(uuid_digitize, tmp_path_factory) -> bytes:
    path = tmp_path_factory.getbasetemp() / uuid_digitize / "raster.zip"
    with open(path, "rb") as file:
        return file.read()


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


@pytest.mark.usefixtures("postgres_container", "redis_container")
@pytest.fixture()
def uuids(map_frame_buffer):
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
