#!/bin/bash
# Run Flask in debug mode
pybabel compile -d sketch_map_tool/translations
flask --app sketch_map_tool/routes.py --debug run --port 8081
