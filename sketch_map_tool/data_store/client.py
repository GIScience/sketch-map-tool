"""Data store client

This module implements a client to a data store.
The data store in use is Redis (Remote Dictionary Service).
Redis is also used as result backend of celery.
"""

from redis import Redis

# from sketch_map_tool.config import get_config


def _get_client():
    # TODO configure
    return Redis(host="localhost", port="6379")


def set(data: dict):
    client = _get_client()
    client.mset(data)


def get(key: str) -> dict:
    client = _get_client()
    return client.get(key)
