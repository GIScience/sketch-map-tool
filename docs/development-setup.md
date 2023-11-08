# Development Setup

## Prerequisites (Requirements)

- Python: `>=3.10`
- [Mamba](https://github.com/conda-forge/miniforge#install): `>=1.4`
- Node: `>=14`

This project uses [Mamba](https://github.com/conda-forge/miniforge#install) for environment and dependencies management. Please make sure it is installed on your system: [Installation Guide](https://github.com/conda-forge/miniforge#install). Instead of Mamba, Conda can also be used.

> Actually, Mamba and Poetry together are used to manage environment and dependencies. But only Mamba is required to be present on the System. Poetry will be installed by Mamba. Mamba installs pre built binaries for depedencies like GDAL. Poetry installs the rest of the Python dependencies.

## Installation

### Python Package

> Note: Editors like IntelliJ IDEA or PyCharm will try to automatically setup Sketch Map Tool.
> This does fail. They will likely create a virtual environment managed by Poetry.
> This is wrong (See prerequisites). If this happens remove the environment (`poetry env remove 3.10`).
> Then execute steps below

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
docker run --name smt-postgres -d -p 5432:5432 -e POSTGRES_PASSWORD=smt -e POSTGRES_USER=smt postgres:15
docker run --name smt-redis -d -p 6379:6379 redis:7

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

## Project Setup using and IDE

If you setup sketch-map-tool in an IDE like PyCharm please make sure that your IDE does not setup a Poetry managed project/virtual environment.
Go thought the setup steps above in the terminal and change interpreter settings in the IDE to point to the mamba/conda environment.

Also make sure the environment variable `PROJ_LIB` to point to the `proj` directory of the mamba/conda environment.
