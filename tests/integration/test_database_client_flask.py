from datetime import datetime
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
def file(sketch_map_marked):
    return FileStorage(stream=BytesIO(sketch_map_marked), filename="my-sketch-map")


@pytest.fixture
def file_2(sketch_map_marked):
    return FileStorage(stream=BytesIO(sketch_map_marked), filename="my-sketch-map-2")


@pytest.fixture
def files(file, file_2):
    return [file, file_2]


@pytest.fixture
def file_ids(files, flask_app):
    """IDs of uploaded files stored in the database."""
    with flask_app.app_context():
        # setup
        file_ids, *_ = db_client_flask.insert_files(files, consent=True)
        yield file_ids
        # teardown
        for id_ in file_ids:
            db_conn = client_flask.open_connection()
            query = "DELETE FROM blob WHERE id = %s"
            with db_conn.cursor() as curs:
                curs.execute(query, [id_])


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


def test_insert_files(flask_app, files, uuid_create, bbox, layer):
    with flask_app.app_context():
        file_ids, uuids, file_names, bboxes, layers = client_flask.insert_files(
            files,
            consent=True,
        )
        assert len(file_ids) == len(uuids) == len(file_names) == 2
        for i, (
            id,
            uuid,
            name,
            bbox_,
            layer_,
        ) in enumerate(
            zip(
                file_ids,
                uuids,
                file_names,
                bboxes,
                layers,
            )
        ):
            assert isinstance(id, int)  # file id
            assert uuid == uuid_create
            assert name == files[i].filename
            assert bbox == bbox_
            assert layer == layer_


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


def test_select_map_frame(flask_app, uuid_create, bbox, layer):
    with flask_app.app_context():
        file = client_flask.select_map_frame(uuid_create)
        assert isinstance(file, bytes)


def test_select_map_frame_file_not_found(flask_app):
    with flask_app.app_context():
        with pytest.raises(CustomFileNotFoundError):
            client_flask.select_map_frame(uuid4())


def test_blob_timestamp(file_ids):
    """Test if timestamp is created when inserting data."""
    query = "SELECT ts FROM blob WHERE id = %s"
    db_conn = client_flask.open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [file_ids[0]])
        raw = curs.fetchone()
    timestamp = raw[0]
    assert isinstance(timestamp, datetime)
