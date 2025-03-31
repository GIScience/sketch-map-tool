#!/bin/bash
# Run celery for development
uv run celery --app sketch_map_tool.tasks worker --concurrency 1 --beat --loglevel=INFO
