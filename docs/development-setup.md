# Development Setup

For contributing to this project please also read the [Contribution Guideline](/CONTRIBUTING.md).

> Note: To just run the tool locally, provide the required [configuration](/docs/configuration.md)
> and use Docker Compose: `docker compose up -d`

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

# compile languages:
pybabel compile -d sketch_map_tool/translations

# install local versions of esbuild, eslint and stylelint to build and check JS and CSS
npm install
npm run build  # build/bundle JS and CSS
```

## Configuration

Please refer to the [configuration documentation](/docs/configuration.md).

> TL;DR: Except of the API token (`SMT-NEPTUNE-API-TOKEN`) for neptune.ai all configuration values come with defaults for development purposes. Please make sure to configure the API token for your environment.

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

## Back-End

### Linter and Formatter

```bash
ruff
ruff format
```

### Exceptions

The use of custom exceptions is highly encouraged.

To translate error messages all custom exceptions should inherit from the `TranslatableError` class (see `exceptions.py`).
A `TranslatableError` should have as first argument a message wrapped in a `N_()` function (see `helper.py`), to mark it for translation, and optionally a dictionary with values for interpolation.

> Note: For more information on translation please see [/docs/translation.md]


### Tests

Provide required [configuration variables](/docs/configuration.md#required-configuration) in `config/test.config.toml`.

To run all tests:
```bash
pytest
```

#### Integration Tests

The integration test suite utilizes the Testcontainers framework to run unique instances of Redis and Postgres for each test session. It also configures and starts Flask and Celery workers in the background.

Many fixtures are written to a temporary directory on disk managed by Pytest. This makes it easy to inspect the results at various steps of the program (E.g. Marking detection pipeline). Unix users usually find this directory under `/tmp/pytest-of-{user}/pytest-current/{uuid}/`. The UUID of requests triggered by the tests (E.g. Create or digitize) is the directory name.

The integration tests will make requests external services. Among others requests are made to HeiGIT Maps (WMS) to retrieve basemap images. Those requests can only be made from HeiGITs internal network.

### Update dependencies

When dependencies changed the environment can be updated by running:

```bash
mamba activate smt
mamba env update --file environment.yml
poetry install
```

## Front-End (HTML, CSS and JS)

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

Also make sure the environment variable `PROJ_LIB` to point to the `proj` directory of the mamba/conda environment:
```bash
PROJ_LIB=/home/$USERDIR/mambaforge/envs/smt/share/proj
```

## Troubleshooting

Make sure that Poetry does not try to manage the virtual environment. Check with `poetry env list`. If any environment are listed remove them: `poetry env remove ...`
