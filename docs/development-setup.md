# Development Setup

## Prerequisites (Requirements)

- Python: `>=3.10`
- [Mamba](https://github.com/conda-forge/miniforge#install): `>=1.4`
- Node: `>=14`

This project uses [Mamba](https://github.com/conda-forge/miniforge#install) for environment and dependencies management. Please make sure it is installed on your system: [Installation Guide](https://github.com/conda-forge/miniforge#install)

> Actually, Mamba and Poetry together are used to manage environment and dependencies. But only Mamba is required to be present on the System. Poetry will be installed by Mamba. Mamba installs pre built binaries for depedencies like GDAL. Poetry installs the rest of the Python dependencies.

## Installation

### Python Package

```bash
# clone repository
git clone https://github.com/GIScience/sketch-map-tool.git
cd sketch-map-tool

# setup environment and install package
mamba env create --file environment.yml

mamba activate smt
poetry install  # poetry installs directly into activated mamba environment

# install git commit hooks
pre-commit install

# fetch and run backend (postgres) and broker (redis) using docker
docker run --name smt-postgres -d -p 5432:5432 -e POSTGRES_PASSWORD=smt -e POSTGRES_USER=smt postgres
docker run --name smt-redis -d -p 6379:6379 redis

# install local versions of esbuild, eslint and stylelint to build and check JS and CSS
npm install
npm run build  # build/bundle JS and CSS
# hack away
```

## Configuration

Please refer to the [configuration documentation](/docs/configuration.md).

## Usage

### 1. Start Celery (Task Queue)

```bash
mamba activate smt
docker start smt-postgres smt-redis
celery --app sketch_map_tool.tasks worker --loglevel=INFO
```

### 2. Start Flask (Web App)

```bash
mamba activate smt
flask --app sketch_map_tool/routes.py --debug run
# Go to http://127.0.0.1:5000
```

## Tests

```bash
# make sure celery is running
pytest
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

## Project Setup for PyCharm

If you like to develop using an IDE like [PyCharm](https://www.jetbrains.com/pycharm/), you can use the PyCharm Run Configurations instead of running Python manually.

1. Add different configurations:
   1. Docker Image Configuration:
      * Image ID: `redis`
      * Container name: `redis`
      * Bind ports: `6379:6379`
   2. Docker Image Configuration:
      * Image ID: `postgres`
      * Container name: `postgres`
      * Bind ports: `5432:5432`
   3. Flask server:
      * Target type: Script path
      * Target: `project_path/sketch_map_tool/routes.py`
   4. Python:
      * Module name: `celery`
      * Parameters: `-A sketch_map_tool.tasks worker`
      * Working directory: `project_path`
      * Before launch: Run Another Configuration for both Docker Image Configurations
   5. Python tests — pytest:
      * Script path: `project_path/tests/unit`
      * Working Directory: `project_path`
2. For development: Run or Debug Celery and Flask Configurations
