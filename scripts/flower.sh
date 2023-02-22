#!/bin/bash
# Run Flower (Celery monitoring tool)
poetry run celery -A sketch_map_tool.tasks flower --broker redis://localhost:6379//
