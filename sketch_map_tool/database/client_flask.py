from uuid import UUID

import psycopg2
from flask import g
from psycopg2.errors import UndefinedTable
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

from sketch_map_tool.config import CONFIG
from sketch_map_tool.exceptions import (
    CustomFileDoesNotExistAnymoreError,
    CustomFileNotFoundError,
    UploadError,
    UUIDNotFoundError,
)
from sketch_map_tool.helpers import N_, to_array
from sketch_map_tool.models import Bbox, MapFrame
from sketch_map_tool.upload_processing import read_qr_code


def open_connection():
    if "db_conn" not in g:
        raw = CONFIG.result_backend
        dns = raw[3:]
        g.db_conn = psycopg2.connect(dns)
        g.db_conn.autocommit = True
    return g.db_conn


def close_connection(e=None):
    db_conn = g.pop("db_conn", None)
    if isinstance(db_conn, connection) and db_conn.closed == 0:  # 0 if the conn is open
        db_conn.close()


def insert_files(
    files,
    consent: bool,
) -> tuple[list[int], list[str], UUID, Bbox, str]:
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
        consent
        )
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

    if len(set(uuids)) > 1:
        raise UploadError(
            N_(
                "You can upload several photos, but they must all show the same area. "
                "These sketch maps cover different areas, "
                "so please upload each area separately."
            )
        )
        # TODO: Remove uploads
    assert len(set(bboxes)) == 1
    assert len(set(layers)) == 1
    uuid = UUID(uuids[0])
    bbox = bboxes[0]
    layer = layers[0]
    return file_ids, file_names, uuid, bbox, layer


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


def select_map_frame_uuid(digitize_uuid: UUID) -> UUID:
    """Get an uploaded file stored in the database by ID."""
    query = "SELECT map_frame_uuid FROM blob WHERE digitize_uuid = %s"
    db_conn = open_connection()
    with db_conn.cursor() as curs:
        curs.execute(query, [str(digitize_uuid)])
        raw = curs.fetchone()
        if raw:
            return UUID(raw[0])
        else:
            raise UUIDNotFoundError(
                N_("There are no files in the database for the uuid: {ID}"),
                {"ID": digitize_uuid},
            )


def select_map_frame(uuid: UUID) -> MapFrame:
    """Select map frame, bbox and layer of the associated UUID."""
    query = """
        SELECT
            uuid,
            file as map_image,
            bbox as bbox_3857,
            bbox_wgs84 as bbox_4326,
            format,
            orientation,
            layer
        FROM map_frame
        WHERE uuid = %s
    """
    db_conn = open_connection()
    with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            cur.execute(query, [str(uuid)])
        except UndefinedTable:
            raise CustomFileNotFoundError(
                N_(
                    "In this Sketch Map Tool instance no sketch map has been "
                    "generated yet. You can only upload sketch "
                    "maps to the instance on which they have been created."
                )
            )
        raw = cur.fetchone()
        if not raw:
            raise CustomFileNotFoundError(
                N_(
                    "There is no map frame in the database with the uuid: {UUID}."
                    " You can only upload sketch maps to the "
                    "instance on which they have been created."
                ),
                {"UUID": uuid},
            )
        if raw["map_image"] is None:
            raise CustomFileDoesNotExistAnymoreError(
                N_("The file with the id: {UUID} does not exist anymore"),
                {"UUID": uuid},
            )
        return MapFrame(**raw)


def update_files_digitize_uuid(file_ids: list[int] | tuple[int], result_uuid: UUID):
    # NOTE: UUID are tracked since release in Mar 3, 2025
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
    # NOTE: downloads are tracked since release in Mar 3, 2025
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
    # NOTE: downloads are tracked since release in Mar 3, 2025
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
    # NOTE: downloads are tracked since release in Mar 3, 2025
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


def select_usage_statistics() -> list[dict]:
    create_query = """
        CREATE OR REPLACE VIEW usage_statistic AS
        SELECT
            sm.uuid,
            sm.bbox,
            sm.bbox_wgs84,
            sm.centroid,
            sm.centroid_wgs84,
            sm.format,
            sm.orientation,
            sm.layer,
            sm.created,
            sm.downloaded,
            sm.iso_a2,
            Coalesce(digitize.uploads, 0::bigint) AS uploads,
            Coalesce(digitize.downloads, 0::bigint) AS downloads,
            Coalesce(digitize.downloads_raster, 0::bigint) AS downloads_raster,
            Coalesce(digitize.downloads_vector, 0::bigint) AS downloads_vector,
            Coalesce(digitize.consenses, 0::bigint) AS consenses
        FROM (
            SELECT
                mf.uuid,
                mf.bbox,
                mf.bbox_wgs84,
                mf.centroid,
                mf.centroid_wgs84,
                mf.format,
                mf.orientation,
                mf.layer,
                mf.created,
                mf.downloaded,
                mf.iso_a2
            FROM
                map_frame mf
            WHERE
                -- old sketch maps do not have enough information stored in DB
                created::date > date '2025-03-04'
            ) sm
            LEFT JOIN (
                SELECT
                    blob.map_frame_uuid AS uuid,
                    Count(*) AS uploads,
                    Sum(
                        CASE WHEN blob.consent THEN
                            1
                        ELSE
                            0
                        END) AS consenses,
                    Sum(
                        CASE WHEN (
                            blob.downloaded_raster IS NOT NULL
                            OR blob.downloaded_vector IS NOT NULL
                        ) THEN
                            1
                        ELSE
                            0
                        END) AS downloads,
                    Sum(
                        CASE WHEN blob.downloaded_raster IS NOT NULL THEN
                            1
                        ELSE
                            0
                        END) AS downloads_raster,
                    Sum(
                        CASE WHEN blob.downloaded_vector IS NOT NULL THEN
                            1
                        ELSE
                            0
                        END) AS downloads_vector
                FROM
                    blob
                WHERE
                    blob.map_frame_uuid IS NOT NULL
                GROUP BY
                    blob.map_frame_uuid) digitize ON digitize.uuid = sm.uuid;
    """
    select_query = "SELECT * FROM usage_statistic ORDER BY created"
    db_conn = open_connection()
    with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(create_query)
        cur.execute(select_query)
        return cur.fetchall()
