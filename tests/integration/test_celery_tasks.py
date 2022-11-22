from io import BytesIO

import pytest

from sketch_map_tool import tasks


def test_generate_sketch_map(celery_worker, bbox, format_, size, scale):
    task = tasks.generate_sketch_map.apply_async(
        args=(bbox, format_, "landscape", size, scale)
    )
    result = task.wait()
    assert isinstance(result, BytesIO)


def test_generate_quality_report(celery_app, celery_worker, bbox_wgs84):
    task = tasks.generate_quality_report.apply_async(args=[bbox_wgs84])
    result = task.wait()
    assert isinstance(result, BytesIO)
