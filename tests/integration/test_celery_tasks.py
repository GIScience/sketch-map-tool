from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from sketch_map_tool import tasks
from sketch_map_tool.database import client_flask
from tests import vcr_app


@vcr_app.use_cassette
def test_generate_sketch_map(bbox, format_, size, scale, layer):
    task = tasks.generate_sketch_map.apply_async(
        args=(
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


@patch("sketch_map_tool.tasks.db_client_celery.cleanup_map_frames")
def test_cleanup_map_frames(mock_cleanup_map_frames):
    # `cleanup_map_frames()` is tested in `test_database_client_celery.py`
    mock_cleanup_map_frames.get.return_value = Mock()
    task = tasks.cleanup_map_frames.apply_async()
    task.wait()


@pytest.mark.usefixtures("uuid_digitize")
@patch("sketch_map_tool.tasks.db_client_celery.cleanup_blob")
def test_cleanup_blobs(mock_cleanup_blob, uuid_create, flask_app):
    # `cleanup_blobs()` is tested in `test_database_client_celery.py`
    mock_cleanup_blob.get.return_value = Mock()
    with flask_app.app_context():
        with client_flask.open_connection().cursor() as curs:
            curs.execute("SELECT id FROM blob WHERE map_frame_uuid = %s", [uuid_create])
            file_ids = curs.fetchall()[0]
    task = tasks.cleanup_blobs.apply_async(file_ids)
    task.wait()
