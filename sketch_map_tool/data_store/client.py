"""Data store client

This module implements a client to a data store.
The data store in use is Redis (Remote Dictionary Service).
Redis is also used as result backend of celery.
"""

from __future__ import annotations

import json
from typing import Dict, get_args

import redis

from sketch_map_tool.config import get_config_value
from sketch_map_tool.definitions import ALLOWED_TYPES, DIGITIZE_TYPES


def _get_client() -> redis.Redis:
    return redis.from_url(get_config_value("data-store"))


def set(data: Dict[str, str]):
    client = _get_client()
    client.mset(data)


def get(key: str) -> str:
    client = _get_client()
    return client.get(key)


def get_task_id(uuid: str, type_: ALLOWED_TYPES) -> int:
    """Get the celery task id from the data store using the request id and type."""
    if type_ in list(get_args(DIGITIZE_TYPES)):
        # Task id equals request uuid (/digitize/results)
        return uuid
    # Get task id from data-store (/create/results)
    raw = get(str(uuid))
    if raw is None:
        raise KeyError("There are no tasks in the broker for UUID: " + uuid)
    request_task = json.loads(raw)
    try:
        task_id = request_task[type_]
    except KeyError as error:
        raise KeyError("There are no tasks in the broker for type: " + type_) from error
    return task_id
