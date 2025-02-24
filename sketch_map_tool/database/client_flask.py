from uuid import UUID

import psycopg2
from flask import g
from psycopg2.errors import UndefinedTable
from psycopg2.extensions import connection
from werkzeug.utils import secure_filename

from sketch_map_tool.config import get_config_value
from sketch_map_tool.exceptions import (
    CustomFileDoesNotExistAnymoreError,
    CustomFileNotFoundError,
)
from sketch_map_tool.helpers import N_, to_array
from sketch_map_tool.models import Bbox, Layer
from sketch_map_tool.upload_processing import read_qr_code


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


def insert_files(
    files, consent: bool
) -> tuple[list[int], list[str], list[str], list[Bbox], list[Layer]]:
    """Insert uploaded files as blob into the database and return ID, UUID and name.

    UUID is derived from decoding the qr-code.
    """
    create_query = """
    CREATE TABLE IF NOT EXISTS blob(
        id SERIAL PRIMARY KEY,
        map_frame_uuid UUID,
        file_name VARCHAR,
        file BYTEA,
        consent BOOLEAN,
        ts TIMESTAMP WITH TIME ZONE DEFAULT now(),
        digitize_uuid UUID,
        downloaded_vector TIMESTAMP WITH TIME ZONE,
        downloaded_raster TIMESTAMP WITH TIME ZONE
        )
    """
    insert_query = """
    INSERT INTO blob (
        map_frame_uuid,
        file_name,
        file,
        consent)
    VALUES (
        %s,
        %s,
        %s,
        %s)
    RETURNING
        id,
        map_frame_uuid,
        file_name
    """
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(create_query)
        file_ids = []
        uuids = []
        file_names = []
        bboxes = []
        layers = []
        for file in files:
            file_content = file.read()
            qr_code_content = read_qr_code(to_array(file_content))
            curs.execute(
                insert_query,
                (
                    qr_code_content["uuid"],
                    secure_filename(file.filename),
                    file_content,
                    consent,
                ),
            )
            result = curs.fetchone()
            if result is None:
                raise ValueError()
            file_ids.append(result[0])
            uuids.append(result[1])
            file_names.append(result[2])
            bboxes.append(qr_code_content["bbox"])
            layers.append(qr_code_content["layer"])
    return file_ids, uuids, file_names, bboxes, layers


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
                N_("There is no file in the database with the id: {ID}"), {"ID": id_}
            )


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
                N_("There is no file in the database with the id: {ID}"), {"ID": id_}
            )


def select_map_frame(uuid: UUID) -> tuple[bytes, str, str]:
    """Select map frame, bbox and layer of the associated UUID."""
    query = "SELECT file FROM map_frame WHERE uuid = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        try:
            curs.execute(query, [str(uuid)])
        except UndefinedTable:
            raise CustomFileNotFoundError(
                N_(
                    "In this Sketch Map Tool instance no sketch map has been "
                    "generated yet. You can only upload sketch "
                    "maps to the instance on which they have been created."
                )
            )
        raw = curs.fetchone()
        if raw:
            if raw[0] is None:
                raise CustomFileDoesNotExistAnymoreError(
                    N_("The file with the id: {UUID} does not exist anymore"),
                    {"UUID": uuid},
                )
            return raw[0]
        else:
            raise CustomFileNotFoundError(
                N_(
                    "There is no map frame in the database with the uuid: {UUID}."
                    " You can only upload sketch maps to the "
                    "instance on which they have been created."
                ),
                {"UUID": uuid},
            )


def update_files_digitize_uuid(file_ids: list[int] | tuple[int], result_uuid: UUID):
    update_query = """
    UPDATE
        blob
    SET
        digitize_uuid = %s
    WHERE
        id = ANY(%s)
    """
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(update_query, [result_uuid, file_ids])


def update_files_download_vector(result_uuid: UUID):
    update_query = """
    UPDATE
        blob
    SET
        downloaded_vector = now()
    WHERE
        digitize_uuid = %s
    """
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(update_query, [result_uuid])


def update_files_download_raster(result_uuid: UUID):
    update_query = """
    UPDATE
        blob
    SET
        downloaded_raster = now()
    WHERE
        digitize_uuid = %s
    """
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(update_query, [result_uuid])


def update_map_frame_downloaded(uuid: UUID):
    update_query = """
    UPDATE
        map_frame
    SET
        downloaded = now()
    WHERE
        uuid = %s
    """
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(update_query, [uuid])
