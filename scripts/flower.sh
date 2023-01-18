#!/bin/bash
# Run Flower (Celery monitoring tool)
celery -A sketch_map_tool.tasks flower --broker redis://localhost:6379//
