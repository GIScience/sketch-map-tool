from unittest.mock import patch
from uuid import uuid4

from sketch_map_tool.database import client


def test_create_connection():
    client.create_connection()


@patch("sketch_map_tool.database.client.db_conn", client.create_connection())
def test_insert_uuid_map(uuid):
    map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
    client._insert_id_map(uuid, map_)
    client._delete_id_map(uuid)


@patch("sketch_map_tool.database.client.db_conn", client.create_connection())
def test_delete_uuid_map(uuid):
    map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
    client._insert_id_map(uuid, map_)
    client._delete_id_map(uuid)


@patch("sketch_map_tool.database.client.db_conn", client.create_connection())
def test_select_uuid_map(uuid):
    map_ = {"sketch-map": str(uuid4()), "quality-report": str(uuid4())}
    client._insert_id_map(uuid, map_)
    client._select_id_map(uuid)
    client._delete_id_map(uuid)


@patch("sketch_map_tool.database.client.db_conn", client.create_connection())
def test_get_async_result_id(uuid):
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())
    map_ = {"sketch-map": uuid1, "quality-report": uuid2}
    client._insert_id_map(uuid, map_)
    assert uuid1 == client.get_async_result_id(uuid, "sketch-map")
    assert uuid2 == client.get_async_result_id(uuid, "quality-report")
    client._delete_id_map(uuid)


@patch("sketch_map_tool.database.client.db_conn", client.create_connection())
def test_insert_files(files):
    client._insert_files(files)
