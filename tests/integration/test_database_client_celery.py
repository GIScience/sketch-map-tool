from uuid import uuid4

import pytest
from psycopg2.extensions import connection

from sketch_map_tool.database import client_celery, client_flask
from sketch_map_tool.exceptions import CustomFileNotFoundError


def test_open_connection():
    client_celery.db_conn = None
    client_celery.open_connection()
    assert isinstance(client_celery.db_conn, connection)


def test_close_closed_connection():
    client_celery.db_conn = None
    client_celery.close_connection()
    assert client_celery.db_conn is None
    client_celery.open_connection()


def test_close_open_connection():
    assert isinstance(client_celery.db_conn, connection)
    client_celery.close_connection()
    assert client_celery.db_conn.closed != 0  # 0 if the connection is open
    client_celery.open_connection()


def test_write_map_frame(flask_app, map_frame, bbox, format_, orientation, layer):
    uuid = uuid4()
    client_celery.insert_map_frame(map_frame, uuid, bbox, format_, orientation, layer)
    with flask_app.app_context():
        file, bbox, layer = client_flask.select_map_frame(uuid)
        assert isinstance(file, bytes)
        assert bbox == str(bbox)
        assert layer == (layer)


def test_delete_map_frame(flask_app, map_frame, bbox, format_, orientation, layer):
    uuid = uuid4()
    client_celery.insert_map_frame(map_frame, uuid, bbox, format_, orientation, layer)
    with flask_app.app_context():
        # do not raise a FileNotFoundError_
        client_flask.select_map_frame(uuid)
    client_celery.delete_map_frame(uuid)
    with pytest.raises(CustomFileNotFoundError):
        with flask_app.app_context():
            client_flask.select_map_frame(uuid)
