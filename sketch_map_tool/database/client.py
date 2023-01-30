import json
from io import BytesIO

import psycopg2
from psycopg2.extensions import connection
from werkzeug.utils import secure_filename

from sketch_map_tool.config import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import FileNotFoundError_, UUIDNotFoundError

db_conn: connection | None = None


def open_connection():
    global db_conn
    raw = get_config_value("result-backend")
    dns = raw[3:]
    db_conn = psycopg2.connect(dns)
    db_conn.autocommit = True


def close_connection():
    global db_conn
    if isinstance(db_conn, connection) and db_conn.closed == 0:  # 0 if the conn is open
        db_conn.close()


class DbConn:
    """
    Context manager for database connection.

    This context manager is intended to be used in the flask worker.
    Celery manages connection to the database during initialization of the workers.
    """

    def __enter__(self):
        open_connection()

    def __exit__(self, exc_type, exc_value, exc_tb):
        close_connection()


# QUERIES
#
def _insert_id_map(uuid: str, map_: dict):
    create_query = """
    CREATE TABLE IF NOT EXISTS uuid_map(
      uuid uuid PRIMARY KEY,
      map json NOT NULL
    )
    """
    insert_query = "INSERT INTO uuid_map(uuid, map) VALUES (%s, %s)"
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        curs.execute(insert_query, [uuid, json.dumps(map_)])


def _delete_id_map(uuid: str):
    query = "DELETE FROM uuid_map WHERE uuid = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [uuid])


def _select_id_map(uuid) -> dict:
    global db_conn
    query = "SELECT map FROM uuid_map WHERE uuid = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [uuid])
        raw = curs.fetchall()
    if raw:
        return raw[0][0]
    else:
        raise UUIDNotFoundError("There are no tasks in the broker for UUID: " + uuid)


def _insert_files(files) -> list[int]:
    """Insert uploaded files as blob into the database and return primary keys"""
    create_query = """
    CREATE TABLE IF NOT EXISTS blob(
        id SERIAL PRIMARY KEY,
        file_name VARCHAR,
        file BYTEA
        )
        """
    insert_query = "INSERT INTO blob(file_name, file) VALUES (%s, %s) RETURNING id"
    data = [(secure_filename(file.filename), file.read()) for file in files]
    with db_conn.cursor() as curs:
        # executemany and fetchall does not work together
        curs.execute(create_query)
        ids = []
        for d in data:
            curs.execute(insert_query, d)
            ids.append(curs.fetchone()[0])
    return ids


def _select_file(id_: int) -> BytesIO:
    query = "SELECT file FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            return BytesIO(raw[0])
        else:
            raise FileNotFoundError_(
                "There is no file in the database with the id: " + str(id_)
            )


def _delete_file(id_: int):
    query = "DELETE FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])


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


def read_file(id_: int) -> memoryview:
    """Get an uploaded file stored in the database by ID."""
    return _select_file(id_)


def write_files(files) -> list[int]:
    """Write uploaded files to the database and return IDs (primary keys)"""
    return _insert_files(files)
