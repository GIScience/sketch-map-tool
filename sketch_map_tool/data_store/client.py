"""Data store client

This module implements a client to a data store.
The data store in use is Redis (Remote Dictionary Service).
Redis is also used as result backend of celery.
"""

from __future__ import annotations

import json

import redis

from sketch_map_tool.config import get_config_value
from sketch_map_tool.definitions import REQUEST_TYPES


def _get_client() -> redis.Redis:
    return redis.from_url(get_config_value("data-store"))


def set(data: dict[str, str]):
    client = _get_client()
    client.mset(data)


def get(key: str) -> str:
    client = _get_client()
    return client.get(key)


def get_task_id(uuid: str, type_: REQUEST_TYPES) -> int:
    """Get the celery task id from the data store using the request id and type."""
    raw = get(str(uuid))
    if raw is None:
        raise KeyError("There are no tasks in the broker for UUID: " + uuid)
    request_task = json.loads(raw)
    try:
        return request_task[type_]  # AsyncResult ID
    except KeyError as error:
        raise KeyError("There are no tasks in the broker for type: " + type_) from error
