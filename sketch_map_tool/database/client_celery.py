import logging
from io import BytesIO
from uuid import UUID

import psycopg2
from psycopg2.errors import UndefinedTable
from psycopg2.extensions import connection

from sketch_map_tool import __version__
from sketch_map_tool.config import get_config_value
from sketch_map_tool.exceptions import (
    CustomFileDoesNotExistAnymoreError,
    CustomFileNotFoundError,
)
from sketch_map_tool.helpers import N_
from sketch_map_tool.models import Bbox, Layer, PaperFormat

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


def insert_map_frame(
    file: BytesIO,
    uuid: UUID,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    layer: Layer,
    aruco: bool,
):
    """Insert map frame alongside map generation parameters into the database.

    The UUID is the primary key.
    The map frame is needed for georeferencing the uploaded files (sketch maps).
    """
    create_query = """
        CREATE TABLE IF NOT EXISTS map_frame(
            uuid UUID PRIMARY KEY,
            file BYTEA,
            bbox VARCHAR,
            lat FLOAT,
            lon FLOAT,
            format VARCHAR,
            orientation VARCHAR,
            layer VARCHAR,
            version VARCHAR,
            aruco BOOLEAN DEFAULT FALSE,
            ts TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
    """
    insert_query = """
        INSERT INTO map_frame (
            uuid,
            file,
            bbox,
            lat,
            lon,
            format,
            orientation,
            layer,
            aruco,
            version
            )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s)
    """
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        curs.execute(
            insert_query,
            (
                str(uuid),
                file.read(),
                str(bbox),
                bbox.centroid[0],
                bbox.centroid[1],
                str(format_),
                orientation,
                layer,
                aruco,
                __version__,
            ),
        )


def cleanup_map_frames():
    """Cleanup map frames which are old and without consent.

    Only set file to null. Keep metadata.
    This function is called by a periodic celery task.
    """
    query = """
    UPDATE
        map_frame
    SET
        file = NULL,
        bbox = NULL
    WHERE
        ts < NOW() - INTERVAL %s
        AND NOT EXISTS (
            SELECT
                *
            FROM
                blob
            WHERE
                map_frame.uuid = blob.map_frame_uuid
                AND consent = TRUE);
    """
    with db_conn.cursor() as curs:
        try:
            curs.execute(query, [get_config_value("cleanup-map-frames-interval")])
        except UndefinedTable:
            logging.info("Table `map_frame` does not exist yet. Nothing todo.")


def cleanup_blob(file_ids: list[int] | tuple[int]):
    """Cleanup uploaded files (sketch maps) without consent.

    Only set file and name to null. Keep metadata.
    This function is called after digitization.
    """
    query = """
    UPDATE
        blob
    SET
        file = NULL,
        file_name = NULL
    WHERE
        id = %s
        AND consent = FALSE;
    """
    with db_conn.cursor() as curs:
        try:
            curs.executemany(query, [[i] for i in file_ids])
        except UndefinedTable:
            logging.info("Table `blob` does not exist yet. Nothing todo.")


def select_file(id_: int) -> bytes:
    """Get an uploaded file stored in the database by ID."""
    query = "SELECT file FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
        raw = curs.fetchone()
        if raw:
            if raw[0] is None:
                raise CustomFileDoesNotExistAnymoreError(
                    N_("The file with the id: {ID} does not exist anymore"), {"ID": id_}
                )
            return raw[0]
        else:
            raise CustomFileNotFoundError(
                N_("There is no file in the database with the id: {ID}"), {"ID": id_}
            )


def delete_file(id_: int):
    query = "DELETE FROM blob WHERE id = %s"
    with db_conn.cursor() as curs:
        curs.execute(query, [id_])
