import logging
from datetime import timedelta

from celery import Celery
from flask import Flask

from sketch_map_tool.config import get_config_value
from sketch_map_tool.database import client_flask as db_client

__version__ = "1.1.4"

waitress_logger = logging.getLogger("waitress")
waitress_logger.setLevel(logging.INFO)


def make_flask() -> Flask:
    flask_app = Flask(__name__)

    flask_app.config.update(
        CELERY_CONFIG={
            "broker_url": get_config_value("broker-url"),
            "result_backend": get_config_value("result-backend"),
            "task_serializer": "pickle",
            "task_track_started": True,  # report ‘started’ status worker executes task
            "task_send_sent_event": True,
            "result_serializer": "pickle",
            "result_extended": True,  # save result attributes to backend (e.g. name)
            "result_compression": "gzip",
            "result_chord_join_timeout": 10.0,  # default: 3.0 seconds
            "result_chord_retry_interval": 3.0,  # default: 1.0 seconds
            # A built-in periodic task will delete the results after this time,
            # assuming that celery beat is enabled.
            "result_expires": timedelta(days=1),
            "accept_content": ["application/json", "application/x-python-serialize"],
            # Reserve at most one extra task for every worker process.
            "worker_prefetch_multiplier": 1,
            "worker_send_task_events": True,  # send task-related events to be monitored
            # Avoid errors due to cached db connections going stale through inactivity
            "database_short_lived_sessions": True,
        }
    )
    flask_app.teardown_appcontext(db_client.close_connection)

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
