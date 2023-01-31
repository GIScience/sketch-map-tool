from uuid import uuid4

import pytest
from psycopg2.extensions import connection

from sketch_map_tool.database import client
from sketch_map_tool.exceptions import FileNotFoundError_


def test_open_connection():
    client.db_conn = None
    client.open_connection()
    assert isinstance(client.db_conn, connection)
    client.close_connection()
    client.db_conn = None


def test_close_closed_connection():
    client.db_conn = None
    client.close_connection()
    assert client.db_conn is None


def test_close_open_connection(db_conn):
    assert isinstance(client.db_conn, connection)
    client.close_connection()
    assert client.db_conn.closed != 0  # 0 if the connection is open


def test_DbConn():
    assert client.db_conn is None or client.db_conn != 0
    with client.DbConn():
        assert isinstance(client.db_conn, connection)
        assert client.db_conn.closed == 0  # 0 if the connection is open
    assert client.db_conn.closed != 0


def test_insert_uuid_map(uuid, db_conn):
    map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
    client._insert_id_map(uuid, map_)
    client._delete_id_map(uuid)


def test_delete_uuid_map(uuid, db_conn):
    map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
    client._insert_id_map(uuid, map_)
    client._delete_id_map(uuid)


def test_select_uuid_map(uuid, db_conn):
    map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
    client._insert_id_map(uuid, map_)
    client._select_id_map(uuid)
    client._delete_id_map(uuid)


def test_get_async_result_id(uuid, db_conn):
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())
    map_ = {"sketch-map": uuid1, "quality-report": uuid2}
    client._insert_id_map(uuid, map_)
    assert uuid1 == client.get_async_result_id(uuid, "sketch-map")
    assert uuid2 == client.get_async_result_id(uuid, "quality-report")
    client._delete_id_map(uuid)


def test_insert_files(files, db_conn):
    ids = client.insert_files(files)
    try:
        assert len(ids) == 2
        assert isinstance(ids[0], int)
    finally:
        # tear down
        for i in ids:
            client.delete_file(i)


def test_delete_file(files, db_conn):
    ids = client.insert_files(files)
    for i in ids:
        # No error should be raised
        client.delete_file(i)


def test_select_file(file_ids, db_conn):
    file = client.select_file(file_ids[0])
    assert isinstance(file, bytes)


def test_select_file_file_not_found(files, db_conn):
    with pytest.raises(FileNotFoundError_):
        client.select_file(1000000)


def test_select_file_name(file_ids, db_conn):
    file = client.select_file_name(file_ids[0])
    assert isinstance(file, str)


def test_select_map_frame(uuids, db_conn):
    file = client.select_map_frame(uuids[0])
    assert isinstance(file, bytes)


def test_select_map_frame_file_not_found(db_conn):
    with pytest.raises(FileNotFoundError_):
        client.select_map_frame(uuid4())


def test_write_map_frame(map_frame_buffer, db_conn):
    uuid = uuid4()
    client.insert_map_frame(map_frame_buffer, uuid)
    try:
        file = client.select_map_frame(uuid)
        assert isinstance(file, bytes)
    finally:
        # tear down
        client.delete_map_frame(uuid)


def test_delete_map_frame(map_frame_buffer, db_conn):
    uuid = uuid4()
    client.insert_map_frame(map_frame_buffer, uuid)
    client.select_map_frame(uuid)  # Should not raise a FileNotFoundError_
    client.delete_map_frame(uuid)
    with pytest.raises(FileNotFoundError_):
        client.select_map_frame(uuid)
