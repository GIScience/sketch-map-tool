#!/bin/bash
# Run Flask in debug mode
poetry run flask --app sketch_map_tool/routes.py --debug run --port 8081
