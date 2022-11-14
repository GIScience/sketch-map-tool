# Development Setup

## Requirements

- Python: `^3.10`
- Poetry: `1.2`
- Node: `>=14`
- Redis: `^7.0`
- Postgres: `^15.0`

This project uses [Poetry](https://python-poetry.org/docs/) for packaging and dependencies management. Please make sure it is installed on your system.

## Installation

### Python Package

```bash
# Git clone repository
poetry install
poetry shell  # Spawns a shell within the virtual environment
pre-commit install  # Install pre-commit hooks
npm install # Install local versions of esbuild, eslint and stylelint to build and check JS and CSS
# Hack away
```

### Celery Backend (Postgres) and Brocker (Redis)

```bash
docker run --name redis -d -p 6379:6379 redis
docker run --name postgres -d -p 5432:5432 -e POSTGRES_PASSWORD=smt -e POSTGRES_USER=smt postgres
```

## Usage

```bash
celery --app sketch_map_tool.tasks worker --loglevel=INFO
flask --app sketch_map_tool/app.py --debug run
# Go to http://127.0.0.1:5000
```

## JS and CSS

For the individual html pages the js and css code should be developed in `client-src/**` as 
ES6 modules. 

To use the code in the HTML Templates it must be build (bundled). The bundler 
([esbuild](https://esbuild.github.io/)) will write the result to `static/bundles/**` 
such that it will be provided by Flask to the web and can be referenced from the HTML Templates.

If you want to add new code for additional HTML pages add entry-points in the build script 
[esbuild.js](../esbuild.js)

Bundle the code with:
```bash
npm run build
```
