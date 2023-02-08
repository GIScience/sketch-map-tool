import json
from io import BytesIO
from uuid import UUID

import psycopg2
from psycopg2.extensions import connection
from werkzeug.utils import secure_filename

from sketch_map_tool.config import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import FileNotFoundError_, UUIDNotFoundError

db_conn: connection | None = None


def bytea2bytes(value, cur):
    """Cast memoryview to binary."""
    m = psycopg2.BINARY(value, cur)
    if m is not None:
        return m.tobytes()


# psycopg2 returns memoryview when reading blobs from DB. We need binary since
# memoryview can not be pickled which is a requirement for result of a celery task.
BYTEA2BYTES = psycopg2.extensions.new_type(
    psycopg2.BINARY.values, "BYTEA2BYTES", bytea2bytes
)
psycopg2.extensions.register_type(BYTEA2BYTES)


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
    query = "SELECT map FROM uuid_map WHERE uuid = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [uuid])
        raw = curs.fetchall()
    if raw:
        return raw[0][0]
    else:
        raise UUIDNotFoundError("There are no tasks in the broker for UUID: " + uuid)


def get_async_result_id(request_uuid: str, request_type: REQUEST_TYPES) -> str:
    """Get the Celery Async Result IDs for a request."""
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
    """Set the Celery Result IDs for a request."""
    _insert_id_map(request_uuid, map_)


def insert_files(files) -> list[int]:
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


def select_file(id_: int) -> bytes:
    """Get an uploaded file stored in the database by ID."""
    query = "SELECT file FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            return raw[0]
        else:
            raise FileNotFoundError_(
                "There is no file in the database with the id: " + str(id_)
            )


def select_file_name(id_: int) -> str:
    """Get an uploaded file name of a file stored in the database by ID."""
    query = "SELECT file_name FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            return raw[0]
        else:
            raise FileNotFoundError_(
                "There is no file in the database with the id: " + str(id_)
            )


def delete_file(id_: int):
    query = "DELETE FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])


def insert_map_frame(file: BytesIO, uuid: UUID):
    """Insert map frame as blob into the database with the uuid as primary key.

    The map frame is later on needed for georeferencing the uploaded photo or scan of
    a sketch map.
    """
    create_query = """
    CREATE TABLE IF NOT EXISTS map_frame(
        uuid UUID PRIMARY KEY,
        file BYTEA
        )
        """
    insert_query = "INSERT INTO map_frame(uuid, file) VALUES (%s, %s)"
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        curs.execute(insert_query, (str(uuid), file.read()))


def select_map_frame(uuid: UUID) -> bytes:
    """Select map frame of the associated UUID."""
    query = "SELECT file FROM map_frame WHERE uuid = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [str(uuid)])
        raw = curs.fetchone()
        if raw:
            return raw[0]
        else:
            raise FileNotFoundError_(
                "There is no map frame in the database with the uuid: {}".format(uuid)
            )


def delete_map_frame(uuid: UUID):
    """Delete map frame of the associated UUID from the database."""
    query = "DELETE FROM map_frame WHERE uuid = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [str(uuid)])
