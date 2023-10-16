import json
from uuid import UUID

import psycopg2
from flask import g
from psycopg2.extensions import connection
from werkzeug.utils import secure_filename

from sketch_map_tool.config import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import (
    CustomFileNotFoundError,
    UUIDNotFoundError,
)


def open_connection():
    if "db_conn" not in g:
        raw = get_config_value("result-backend")
        dns = raw[3:]
        g.db_conn = psycopg2.connect(dns)
        g.db_conn.autocommit = True
    return g.db_conn


def close_connection(e=None):
    db_conn = g.pop("db_conn", None)
    if isinstance(db_conn, connection) and db_conn.closed == 0:  # 0 if the conn is open
        db_conn.close()


def _insert_id_map(uuid: str, map_: dict):
    create_query = """
    CREATE TABLE IF NOT EXISTS uuid_map(
      uuid uuid PRIMARY KEY,
      map json NOT NULL
    )
    """
    insert_query = "INSERT INTO uuid_map(uuid, map) VALUES (%s, %s)"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        curs.execute(insert_query, [uuid, json.dumps(map_)])


def _delete_id_map(uuid: str):
    query = "DELETE FROM uuid_map WHERE uuid = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [uuid])


def _select_id_map(uuid) -> dict:
    query = "SELECT map FROM uuid_map WHERE uuid = %s"
    db_conn = open_connection()
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
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        ids = []
        for file in files:
            curs.execute(insert_query, (secure_filename(file.filename), file.read()))
            ids.append(curs.fetchone()[0])
    return ids


def select_file(id_: int) -> bytes:
    """Get an uploaded file stored in the database by ID."""
    query = "SELECT file FROM blob WHERE id = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            return raw[0]
        else:
            raise CustomFileNotFoundError(
                "There is no file in the database with the id: " + str(id_)
            )


def delete_file(id_: int):
    query = "DELETE FROM blob WHERE id = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])


def select_file_name(id_: int) -> str:
    """Get an uploaded file name of a file stored in the database by ID."""
    query = "SELECT file_name FROM blob WHERE id = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            return raw[0]
        else:
            raise CustomFileNotFoundError(
                "There is no file in the database with the id: " + str(id_)
            )


def select_map_frame(uuid: UUID) -> bytes:
    """Select map frame of the associated UUID."""
    query = "SELECT file FROM map_frame WHERE uuid = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        try:
            curs.execute(query, [str(uuid)])
        except psycopg2.errors.UndefinedTable:
            raise CustomFileNotFoundError(
                "In this Sketch Map Tool instance no sketch map "
                "has been generated yet. You can only upload sketch"
                " maps to the instance on which they have been created."
            )
        raw = curs.fetchone()
        if raw:
            return raw[0]
        else:
            raise CustomFileNotFoundError(
                f"There is no map frame in the database with the uuid: {uuid}."
                f" You can only upload sketch maps to the "
                "instance on which they have been created."
            )


def delete_map_frame(uuid: UUID):
    """Delete map frame of the associated UUID from the database."""
    query = "DELETE FROM map_frame WHERE uuid = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [str(uuid)])
