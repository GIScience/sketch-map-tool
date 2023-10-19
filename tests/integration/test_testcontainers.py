from celery.contrib.testing.tasks import ping  # noqa: F401
from psycopg2.extensions import connection

from sketch_map_tool.config import get_config_value
from sketch_map_tool.database import client_celery


def test_testcontainers_postgres():
    conn = get_config_value("result-backend")
    # test that connection string is set and not default
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


def test_testcontainers_redis():
    conn = get_config_value("broker-url")
    # test that connection string is set and not default
    assert conn != "redis://localhost:6379"
    assert conn != ""
    assert conn is not None
