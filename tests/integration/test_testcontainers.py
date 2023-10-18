import pytest
from celery.contrib.testing.tasks import ping  # noqa: F401
from psycopg2.extensions import connection
from testcontainers.postgres import PostgresContainer

from sketch_map_tool import CELERY_CONFIG
from sketch_map_tool import celery_app as ca
from sketch_map_tool.config import get_config_value
from sketch_map_tool.database import client_celery
from sketch_map_tool.tasks import generate_quality_report
from tests import vcr_app


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="session", autouse=True)
def postgres_container(monkeypatch_session):
    with PostgresContainer("postgres:15") as postgres:
        conn = "db+postgresql://{user}:{password}@localhost:{port}/{database}".format(
            user=postgres.POSTGRES_USER,
            password=postgres.POSTGRES_PASSWORD,
            port=postgres.get_exposed_port(5432),
            database=postgres.POSTGRES_DB,
        )
        monkeypatch_session.setenv("SMT-RESULT-BACKEND", conn)
        print(conn)
        # pytestmark = pytest.mark.glob("celery", result_backend=conn)

        yield {"connection_url": conn}
    # cleanup


@pytest.fixture(scope="session")
def celery_config(postgres_container):
    CELERY_CONFIG["result_backend"] = postgres_container["connection_url"]
    return CELERY_CONFIG


@pytest.fixture(scope="session")
def celery_app(celery_config):
    ca.conf.update(celery_config)
    return ca


def test_testcontainers():
    # test that connection string is set and not default
    conn = get_config_value("result-backend")
    assert conn != "db+postgresql://smt:smt@localhost:5432"
    assert conn != ""
    assert conn is not None

    client_celery.db_conn = None
    client_celery.open_connection()
    assert isinstance(client_celery.db_conn, connection)
    query = "SELECT 1;"
    with client_celery.db_conn.cursor() as curs:
        curs.execute(query)
        raw = curs.fetchone()
        assert raw == (1,)
    client_celery.close_connection()
    client_celery.db_conn = None


@vcr_app.use_cassette
def test_task(bbox_wgs84, celery_worker, celery_app):
    assert generate_quality_report.delay(bbox_wgs84).get() is not None
