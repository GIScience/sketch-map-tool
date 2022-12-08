import json

import psycopg2

from sketch_map_tool.config import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import UUIDNotFoundError


def _create_connection():
    raw = get_config_value("result-backend")
    dns = raw[3:]
    connection = psycopg2.connect(dns)
    connection.autocommit = True
    return connection


def _execute_query(query):
    connection = _create_connection()
    cursor = connection.cursor()

    cursor.execute(query)

    cursor.close()
    connection.close()


def _execute_write_query(query, data):
    connection = _create_connection()
    cursor = connection.cursor()

    cursor.execute(query, data)

    cursor.close()
    connection.close()


def _execute_read_query(query, data):
    connection = _create_connection()
    cursor = connection.cursor()

    cursor.execute(query, data)
    result = cursor.fetchall()

    cursor.close()
    connection.close()
    return result


# QUERIES
#
def _insert_id_map(uuid: str, map_: dict):
    query = """
    CREATE TABLE IF NOT EXISTS uuid_map(
      uuid uuid PRIMARY KEY,
      map json NOT NULL
    )
    """
    _execute_query(query)

    query = "INSERT INTO uuid_map(uuid, map) VALUES (%s, %s)"
    _execute_write_query(query, [uuid, json.dumps(map_)])


def _delete_id_map(uuid: str):
    query = "DELETE FROM uuid_map WHERE uuid = %s"
    _execute_write_query(query, [uuid])


def _select_id_map(uuid) -> dict:
    query = "SELECT map FROM uuid_map WHERE uuid = %s"
    raw = _execute_read_query(query, [uuid])
    if raw:
        return raw[0][0]
    else:
        raise UUIDNotFoundError("There are no tasks in the broker for UUID: " + uuid)


# Set and get request ID and type to Async Result IDs
#
def get_async_result_id(request_uuid: str, request_type: REQUEST_TYPES) -> str:
    """Get the Celery Async Result ID for a request."""
    map_ = _select_id_map(request_uuid)
    try:
        return map_[request_type]  # AsyncResult ID
    except KeyError as error:
        raise UUIDNotFoundError(
            "There are no tasks in the broker for UUID and request type: {}, {}".format(
                request_uuid, request_type
            )
        ) from error


def set_async_result_ids(request_uuid, map_: dict[REQUEST_TYPES, str]):
    _insert_id_map(request_uuid, map_)
