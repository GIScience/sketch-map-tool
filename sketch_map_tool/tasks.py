from sketch_map_tool import celery_app as celery


@celery.task()
def generate_sketchmap(bbox: list, format_: str, orientation: str, size: dict) -> str:
    print("celery task")
    return "Done"
