# Development Setup

## Requirements

- Python: `^3.8`
- Poetry: `1.2`
- Node: `>=14`

This project uses [Poetry](https://python-poetry.org/docs/) for packaging and dependencies management. Please make sure it is installed on your system.

## Installation

```bash
# Git clone repository
poetry install
poetry shell  # Spawns a shell within the virtual environment
pre-commit install  # Install pre-commit hooks
npm install # Install local versions of eslint and stylelint to check JS and CSS
# Hack away
flask --app sketch_map_tool/app.py --debug run
```
