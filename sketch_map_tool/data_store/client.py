"""Data store client

This module implements a client to a data store.
The data store in use is Redis (Remote Dictionary Service).
Redis is also used as result backend of celery.
"""

from __future__ import annotations

from typing import Dict

import redis

from sketch_map_tool.config import get_config_value


def _get_client() -> redis.Redis:
    return redis.from_url(get_config_value("data-store"))


def set(data: Dict[str, str]):
    client = _get_client()
    client.mset(data)


def get(key: str) -> str:
    client = _get_client()
    return client.get(key)
