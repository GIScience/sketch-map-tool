from celery import Celery
from flask import Flask

from sketch_map_tool.config import get_config_value

__version__ = "1.0.0"


def make_flask() -> Flask:
    flask_app = Flask(__name__)

    flask_app.config.update(
        CELERY_CONFIG={
            "broker_url": get_config_value("broker-url"),
            "result_backend": get_config_value("result-backend"),
            "task_serializer": "pickle",
            "result_serializer": "json",
            "result_compression": "gzip",
            "result_chord_join_timeout": 10.0,  # default: 3.0 seconds
            "result_chord_retry_interval": 3.0,  # default: 1.0 seconds
            "accept_content": ["application/json", "application/x-python-serialize"],
            # Reserve at most one extra task for every worker process.
            "worker_prefetch_multiplier": 1,
        }
    )

    return flask_app


def make_celery(flask_app: Flask) -> Celery:
    celery_app = Celery(flask_app.import_name)
    celery_app.conf.update(flask_app.config["CELERY_CONFIG"])

    class ContextTask(celery_app.Task):  # type: ignore
        def __call__(self, *args, **kwargs):  # type: ignore
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


flask_app = make_flask()
celery_app = make_celery(flask_app)
