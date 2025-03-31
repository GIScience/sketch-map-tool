#!/bin/bash
# Run Flower (Celery monitoring tool)
uv run celery -A sketch_map_tool.tasks flower --broker redis://localhost:6379//
