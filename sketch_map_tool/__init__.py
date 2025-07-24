import logging
from datetime import timedelta

from celery import Celery
from flask import Flask, request
from flask_babel import Babel

# import of gdal/osr is because of following issues:
# https://github.com/GIScience/sketch-map-tool/issues/503
from osgeo import gdal, osr  # noqa: F401

from sketch_map_tool.config import get_config_value
from sketch_map_tool.database import client_flask as db_client
from sketch_map_tool.definitions import LANGUAGES

__version__ = "2025.07.24.2"

# Setup logging
LEVEL = getattr(logging, get_config_value("log-level").upper())
FORMAT = "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s"
logging.basicConfig(
    level=LEVEL,
    format=FORMAT,
)

CELERY_CONFIG = {
    "broker_url": get_config_value("broker-url"),
    "result_backend": get_config_value("result-backend"),
    "task_serializer": "pickle",
    "task_track_started": True,  # report ‘started’ status worker executes task
    "task_send_sent_event": True,
    "task_time_limit": 900,  # kill task after 15 minutes
    # Max number of tasks a worker can execute before it’s replaced by a new process.
    # Useful if for memory leaks.
    "worker_max_tasks_per_child": 16,
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
    # give enough time to load models into memory during startup
    "worker_proc_alive_timeout": 120,
    # Avoid errors due to cached db connections going stale through inactivity
    "database_short_lived_sessions": True,
    # Cleanup map frames and uploaded files stored in the database
    "beat_schedule": {
        "cleanup": {
            "task": "sketch_map_tool.tasks.cleanup_map_frames",
            "schedule": timedelta(hours=3),
        },
    },
}


def make_flask() -> Flask:
    flask_app = Flask(__name__)
    flask_app.config.update(
        CELERY_CONFIG=CELERY_CONFIG, BABEL_DEFAULT_LOCALE="en", LANGUAGES=LANGUAGES
    )
    flask_app.teardown_appcontext(db_client.close_connection)
    return flask_app


def make_celery(flask_app: Flask) -> Celery:
    celery_app = Celery(flask_app.import_name)
    celery_app.conf.update(flask_app.config["CELERY_CONFIG"])

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


def get_locale() -> str | None:
    if request.view_args is not None and "lang" in request.view_args.keys():
        # only return if path prefix is a language key (not in the case of /favicon)
        if request.view_args["lang"] in LANGUAGES.keys():
            return request.view_args["lang"]
    return "en"


flask_app = make_flask()
babel = Babel(flask_app, locale_selector=get_locale)  # for translations
celery_app = make_celery(flask_app)
