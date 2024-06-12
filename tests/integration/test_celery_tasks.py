from io import BytesIO
from uuid import UUID, uuid4

import pytest

from sketch_map_tool import tasks
from sketch_map_tool.database.client_flask import open_connection, select_map_frame
from sketch_map_tool.exceptions import CustomFileDoesNotExistAnymoreError
from tests import vcr_app


@vcr_app.use_cassette
def test_generate_sketch_map(bbox, format_, size, scale, layer):
    task = tasks.generate_sketch_map.apply_async(
        args=(
            str(uuid4()),
            bbox,
            format_,
            "landscape",
            size,
            scale,
            layer,
        )
    )
    result = task.wait()
    assert isinstance(result, BytesIO)


@vcr_app.use_cassette
def test_generate_quality_report(bbox_wgs84):
    task = tasks.generate_quality_report.apply_async(args=[bbox_wgs84])
    result = task.wait()
    assert isinstance(result, BytesIO)


@pytest.mark.usefixtures("uuid_digitize")
def test_cleanup_nothing_to_do(uuid_create: str, map_frame: bytes, flask_app):
    with flask_app.app_context():
        task = tasks.cleanup.apply_async()
        task.wait()
        # should not raise an error / should not delete the map frame
        map_frame, _, _ = select_map_frame(UUID(uuid_create))
        assert map_frame == map_frame


@pytest.mark.usefixtures("uuid_digitize")
def test_cleanup_old_map_frame(uuid_create: str, map_frame: bytes, flask_app):
    with flask_app.app_context():
        try:
            # test
            # mock map frame which is uploaded a year ago
            update_query = (
                "UPDATE map_frame SET ts = NOW() - INTERVAL '6 months' WHERE uuid = %s"
            )
            db_conn = open_connection()
            with db_conn.cursor() as curs:
                curs.execute(update_query, [uuid_create])
            task = tasks.cleanup.apply_async()
            task.wait()
            with pytest.raises(CustomFileDoesNotExistAnymoreError):
                # map frame file content should be delete
                select_map_frame(UUID(uuid_create))
        finally:
            # tear down: Due to usage of session scoped fixture
            # map frame needs to be reinstatiated
            update_query = "UPDATE map_frame SET file = %s WHERE uuid = %s"
            with db_conn.cursor() as curs:
                curs.execute(update_query, [map_frame.read(), uuid_create])
