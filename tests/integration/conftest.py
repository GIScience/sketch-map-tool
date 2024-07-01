import json
from io import BytesIO
from uuid import UUID

import fitz
import pytest
from celery.contrib.testing.tasks import ping  # noqa: F401
from flask_babel import Babel
from numpy.typing import NDArray
from PIL import Image, ImageOps
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from sketch_map_tool import CELERY_CONFIG, get_locale, make_flask, routes
from sketch_map_tool import celery_app as smt_celery_app
from sketch_map_tool.config import DEFAULT_CONFIG
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.helpers import to_array
from sketch_map_tool.models import Bbox, Layer, PaperFormat, Size
from sketch_map_tool.upload_processing import clip
from tests import FIXTURE_DIR


#
# Session wide test setup of DB (redis and postgres) and workers (flask and celery)
#
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
        monkeypatch_session.setitem(DEFAULT_CONFIG, "result-backend", conn)
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
        monkeypatch_session.setitem(DEFAULT_CONFIG, "broker-url", conn)
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
    app.add_url_rule("/api/health", view_func=routes.health, methods=["GET"])
    app.add_url_rule("/create", view_func=routes.create, methods=["GET"])
    app.add_url_rule("/digitize", view_func=routes.digitize, methods=["GET"])
    app.add_url_rule("/", view_func=routes.index, methods=["GET"])
    app.add_url_rule("/about", view_func=routes.about, methods=["GET"])
    app.add_url_rule("/help", view_func=routes.help, methods=["GET"])

    Babel(app, locale_selector=get_locale)  # for translations

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
@pytest.fixture(scope="session")
def bbox() -> Bbox:
    return Bbox(
        lon_min=964472.1973848869,
        lat_min=6343459.035638228,
        lon_max=967434.6098457306,
        lat_max=6345977.635778541,
    )


@pytest.fixture
def size() -> Size:
    return Size(width=1867, height=1587)


@pytest.fixture(scope="session")
def format_() -> PaperFormat:
    return PaperFormat(
        "A4",
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


@pytest.fixture(scope="session")
def orientation() -> str:
    return "landscape"


@pytest.fixture
def scale():
    return 10231.143861780083


# TODO:
@pytest.fixture(scope="session", params=["osm"])  # , "esri-world-imagery"])
def layer(request):
    return Layer(request.param)


@pytest.fixture
def uuid():
    return "654dd0d3-7bb0-4a05-8a68-517f0d9fc98e"


@pytest.fixture
def bbox_wgs84():
    return Bbox(lon_min=8.625, lat_min=49.3711, lon_max=8.7334, lat_max=49.4397)


# TODO: Fixture `sketch_map_marked` only works for landscape orientation.
# TODO: Add other params
@pytest.fixture(scope="session")
def params(layer, bbox, format_, orientation):
    return {
        "format": format_.title,
        "orientation": orientation,
        "bbox": "[" + str(bbox) + "]",
        # NOTE: bboxWGS84 is has not the same geographical extent as above bbox
        "bboxWGS84": (
            "[8.66376011761138,49.40266507327297,8.690376214631833,49.41716014123875]"
        ),
        "size": '{"width": 1716,"height": 1436}',
        "scale": "9051.161965312804",
        "layer": layer,
    }


@pytest.fixture(scope="session")
def uuid_create(
    params,
    flask_client,
    flask_app,
    celery_app,
    tmp_path_factory,
) -> str:
    """UUID after request to /create and successful sketch map generation."""
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
    result = task.get(timeout=190)

    # Write sketch map to temporary test directory
    fn = tmp_path_factory.mktemp(uuid, numbered=False) / "sketch-map.pdf"
    with open(fn, "wb") as file:
        file.write(result.getbuffer())

    return uuid


@pytest.fixture(scope="session")
def sketch_map(uuid_create, tmp_path_factory) -> bytes:
    """Sketch Map as PDF."""
    path = tmp_path_factory.getbasetemp() / uuid_create / "sketch-map.pdf"
    with open(path, "rb") as file:
        return file.read()


@pytest.fixture(scope="session")
def map_frame(uuid_create, flask_app, tmp_path_factory) -> BytesIO:
    """Map Frame as PNG."""
    with flask_app.app_context():
        map_frame, _, _ = db_client_flask.select_map_frame(UUID(uuid_create))
    path = tmp_path_factory.getbasetemp() / uuid_create / "map-frame.png"
    with open(path, "wb") as file:
        file.write(map_frame)
    return BytesIO(map_frame)


@pytest.fixture(scope="session")
def sketch_map_marked(uuid_create, sketch_map, tmp_path_factory) -> bytes:
    """Sketch map with markings as PNG."""
    # TODO: increase resolution of PNG
    path = tmp_path_factory.getbasetemp() / uuid_create / "sketch-map-marked.png"

    # Convert PDF to PNG
    pdf = fitz.open(stream=sketch_map)  # type: ignore
    pag = pdf.load_page(0)
    mat = fitz.Matrix(2, 2)
    pag.get_pixmap(matrix=mat).save(path, output="png")

    # Draw shapes on PNG (Sketch Map)
    img1 = Image.open(path)  # Sketch Map (primary image)
    img2 = Image.open(
        FIXTURE_DIR / "upload-processing" / "markings-transparent.png"
    )  # Markings (overlay image)
    img2 = ImageOps.cover(img2, img1.size)  # type: ignore
    img1.paste(img2, (0, 0), mask=img2)  # Overlay images starting at 0, 0

    # Displaying the image
    # img1.show()

    # TODO: what should be the return type of the fixture?
    img1.save(path)
    with open(path, "rb") as file:
        return file.read()


@pytest.fixture(scope="session")
def map_frame_marked(
    flask_app,
    uuid_create,
    sketch_map_marked,
) -> NDArray:
    """Sketch map frame with markings as PNG."""
    with flask_app.app_context():
        map_frame, _, _ = db_client_flask.select_map_frame(UUID(uuid_create))
    return clip(
        to_array(sketch_map_marked),
        to_array(map_frame),
    )


@pytest.fixture(scope="session")
def uuid_digitize(
    sketch_map_marked,
    flask_client,
    flask_app,
    celery_app,
    tmp_path_factory,
) -> str:
    """UUID after uploading files to /digitize and successful result generation."""
    data = {"file": [(BytesIO(sketch_map_marked), "sketch_map.png")], "consent": True}
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
    result_vector = task_vector.get(timeout=190)
    result_raster = task_raster.get(timeout=190)
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
