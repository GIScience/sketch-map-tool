#!/bin/bash
# Run celery events (Curses Monitor)
uv run celery -A sketch_map_tool.tasks events
