#!/bin/bash
# Run celery events (Curses Monitor)
poetry run celery -A sketch_map_tool.tasks events
