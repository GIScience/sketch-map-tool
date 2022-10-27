from time import sleep
from typing import Dict, List, Union

from celery.result import AsyncResult

from sketch_map_tool import celery_app as celery


@celery.task()
def generate_sketch_map(
    bbox: List[float],
    format_: str,
    orientation: str,
    size: Dict[str, float],
) -> Union[str, AsyncResult]:
    sleep(10)  # simulate long running task (10s)
    return "Sketch Map"


@celery.task()
def generate_quality_report(bbox: List[float]) -> Union[str, AsyncResult]:
    sleep(10)  # simulate long running task (10s)
    return "Quality Report"
