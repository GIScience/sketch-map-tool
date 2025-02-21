"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

from sketch_map_tool import tasks
from tests import vcr_app as vcr


@vcr.use_cassette
def test_generate_sketch_map(
    monkeypatch,
    bbox,
    format_,
    size,
    scale,
    layer,
    aruco,
):
    monkeypatch.setattr(
        "sketch_map_tool.tasks.db_client_celery.insert_map_frame",
        lambda *_: None,
    )
    map_pdf = tasks.generate_sketch_map(
        bbox,
        format_,
        "landscape",
        size,
        scale,
        layer,
        aruco,
    )
    assert isinstance(map_pdf, BytesIO)
