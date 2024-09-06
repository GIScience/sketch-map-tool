from io import BytesIO
from uuid import uuid4

import pytest

from sketch_map_tool import tasks
from sketch_map_tool.database import client_flask
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
    result = task.get(timeout=180)
    assert isinstance(result, BytesIO)


@vcr_app.use_cassette
def test_generate_quality_report(bbox_wgs84):
    task = tasks.generate_quality_report.apply_async(args=tuple([bbox_wgs84]))
    result = task.get(timeout=180)
    assert isinstance(result, BytesIO)


@pytest.mark.usefixtures("uuid_create", "uuid_digitize")
def test_cleanup_map_frames():
    # `cleanup_map_frames()` is tested in `test_database_client_celery.py`
    task = tasks.cleanup_map_frames.apply_async()
    task.wait()


@pytest.mark.usefixtures("uuid_digitize")
def test_cleanup_blobs(uuid_create, flask_app):
    # `cleanup_blobs()` is tested in `test_database_client_celery.py`
    with flask_app.app_context():
        with client_flask.open_connection().cursor() as curs:
            curs.execute("SELECT id FROM blob WHERE map_frame_uuid = %s", [uuid_create])
            file_ids = curs.fetchall()[0]
    task = tasks.cleanup_blobs.apply_async(kwargs={"file_ids": file_ids})
    task.wait()
