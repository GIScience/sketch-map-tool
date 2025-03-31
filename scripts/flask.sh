#!/bin/bash
# Run Flask in debug mode
npm run build
uv run pybabel compile -d sketch_map_tool/translations
uv run flask --app sketch_map_tool/routes.py --debug run --port 8081
