from time import sleep

from sketch_map_tool import celery_app as celery


@celery.task()
def generate_sketch_map(bbox: list, format_: str, orientation: str, size: dict) -> str:
    sleep(10)  # simulate long running task (10s)
    return "Sketch Map"


@celery.task()
def generate_quality_report(bbox: list) -> str:
    sleep(10)  # simulate long running task (10s)
    return "Quality Report"
