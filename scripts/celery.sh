#!/bin/bash
# Run celery
poetry run celery --app sketch_map_tool.tasks worker --beat --concurrency 4 --loglevel=INFO
