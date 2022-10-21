#!/bin/bash
celery -A sketch_map_tool.tasks worker --loglevel=INFO
