"""Data store client

This module implements a client to a data store.
The data store in use is Redis (Remote Dictionary Service).
Redis is also used as result backend of celery.
"""

import redis

from sketch_map_tool.config import get_config_value


def _get_client():
    # TODO configure
    return redis.from_url(get_config_value("data-store"))


def set(data: dict):
    client = _get_client()
    client.mset(data)


def get(key: str) -> dict:
    client = _get_client()
    return client.get(key)
