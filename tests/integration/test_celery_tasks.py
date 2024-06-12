from io import BytesIO
from uuid import uuid4

import pytest

from sketch_map_tool import tasks
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


@pytest.mark.usefixtures("uuid_create", "uuid_digitize")
def test_cleanup():
    """Map frame is uploaded recently and uploaded sketch map has consent."""
    task = tasks.cleanup.apply_async()
    task.wait()
