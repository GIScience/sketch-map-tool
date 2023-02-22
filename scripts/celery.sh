#!/bin/bash
# Run celery
poetry run celery -A sketch_map_tool.tasks worker --loglevel=INFO
