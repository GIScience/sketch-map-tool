"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

from sketch_map_tool import tasks
from tests import vcr_app as vcr


@vcr.use_cassette
def test_generate_sketch_map(
    monkeypatch,
    bbox,
    bbox_wgs84,
    format_,
    size,
    scale,
    layer,
):
    monkeypatch.setattr(
        "sketch_map_tool.tasks.db_client_celery.insert_map_frame",
        lambda *_: None,
    )
    map_pdf = tasks.generate_sketch_map(
        bbox,
        bbox_wgs84,
        format_,
        "landscape",
        size,
        scale,
        layer,
    )
    assert isinstance(map_pdf, BytesIO)
