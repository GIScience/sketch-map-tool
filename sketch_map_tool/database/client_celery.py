from io import BytesIO
from uuid import UUID

import psycopg2
from psycopg2.extensions import connection

from sketch_map_tool.config import get_config_value
from sketch_map_tool.exceptions import (
    CustomFileDoesNotExistAnymoreError,
    CustomFileNotFoundError,
)
from sketch_map_tool.helpers import N_

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


def insert_map_frame(file: BytesIO, uuid: UUID):
    """Insert map frame as blob into the database with the uuid as primary key.

    The map frame is later on needed for georeferencing the uploaded photo or scan of
    a sketch map.
    """
    create_query = """
    CREATE TABLE IF NOT EXISTS map_frame(
        uuid UUID PRIMARY KEY,
        file BYTEA,
        ts TIMESTAMP WITH TIME ZONE DEFAULT now()
        )
        """
    insert_query = "INSERT INTO map_frame(uuid, file) VALUES (%s, %s)"
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        curs.execute(insert_query, (str(uuid), file.read()))


def delete_map_frame(uuid: UUID):
    """Delete map frame of the associated UUID from the database."""
    query = "DELETE FROM map_frame WHERE uuid = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [str(uuid)])


def set_map_frame_to_null(uuid: UUID):
    """Set map frame of the associated UUID from the database to null.

    Keep UUID and timestamp in the database.
    """
    # TODO: JOIN with blog to read consent
    query = """
    UPDATE
        map_frame
    SET
        file = NULL
    WHERE
        uuid = %s
        AND ts < NOW() - INTERVAL '6 months'
        AND NOT EXISTS (
            SELECT
                *
            FROM
                blob
            WHERE
                map_frame.uuid = blob.uuid
                AND consent = TRUE);
    """
    with db_conn.cursor() as curs:
        curs.execute(query, [str(uuid)])


def select_file(id_: int) -> bytes:
    """Get an uploaded file stored in the database by ID."""
    query = "SELECT file FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            if raw[0] is None:
                raise CustomFileDoesNotExistAnymoreError(
                    N_("The file with the id: {ID} does not exist anymore"), {"ID", id_}
                )
            return raw[0]
        else:
            raise CustomFileNotFoundError(
                N_("There is no file in the database with the id: {ID}"), {"ID", id_}
            )


def delete_file(id_: int):
    query = "DELETE FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
