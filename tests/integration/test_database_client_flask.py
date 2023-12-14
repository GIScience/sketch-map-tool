from io import BytesIO
from uuid import uuid4

import pytest
from flask import g
from psycopg2.extensions import connection
from werkzeug.datastructures import FileStorage

from sketch_map_tool.database import client_flask
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.exceptions import (
    CustomFileNotFoundError,
)


@pytest.fixture
def file(sketch_map):
    return FileStorage(stream=BytesIO(sketch_map), filename="filename")


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


def test_open_close_connection(flask_app):
    with flask_app.app_context():
        g.pop("db_conn", None)
        db_conn = client_flask.open_connection()
        assert isinstance(db_conn, connection)
        client_flask.close_connection()
        assert db_conn.closed != 0  # 0 if the connection is open


def test_insert_uuid_map(flask_app, uuid):
    with flask_app.app_context():
        map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
        client_flask._insert_id_map(uuid, map_)
        client_flask._delete_id_map(uuid)


def test_delete_uuid_map(flask_app, uuid):
    with flask_app.app_context():
        map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
        client_flask._insert_id_map(uuid, map_)
        client_flask._delete_id_map(uuid)


def test_select_uuid_map(flask_app, uuid):
    with flask_app.app_context():
        map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
        client_flask._insert_id_map(uuid, map_)
        client_flask._select_id_map(uuid)
        client_flask._delete_id_map(uuid)


def test_get_async_result_id(flask_app, uuid):
    with flask_app.app_context():
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        map_ = {"sketch-map": uuid1, "quality-report": uuid2}
        client_flask._insert_id_map(uuid, map_)
        assert uuid1 == client_flask.get_async_result_id(uuid, "sketch-map")
        assert uuid2 == client_flask.get_async_result_id(uuid, "quality-report")
        client_flask._delete_id_map(uuid)


def test_insert_files(flask_app, files):
    with flask_app.app_context():
        ids = client_flask.insert_files(files)
        try:
            assert len(ids) == 2
            assert isinstance(ids[0], int)
        finally:
            # tear down
            for i in ids:
                client_flask.delete_file(i)


def test_delete_file(flask_app, files):
    with flask_app.app_context():
        ids = client_flask.insert_files(files)
        for i in ids:
            # No error should be raised
            client_flask.delete_file(i)


def test_select_file(file_ids):
    file = client_flask.select_file(file_ids[0])
    assert isinstance(file, bytes)


def test_select_file_file_not_found(flask_app, files):
    with flask_app.app_context():
        with pytest.raises(CustomFileNotFoundError):
            client_flask.select_file(1000000)


def test_select_file_name(file_ids):
    file = client_flask.select_file_name(file_ids[0])
    assert isinstance(file, str)


def test_select_map_frame(flask_app, uuid_create):
    with flask_app.app_context():
        file = client_flask.select_map_frame(uuid_create)
        assert isinstance(file, bytes)


def test_select_map_frame_file_not_found(flask_app):
    with flask_app.app_context():
        with pytest.raises(CustomFileNotFoundError):
            client_flask.select_map_frame(uuid4())
