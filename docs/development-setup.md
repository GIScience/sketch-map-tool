# Development Setup

For contributing to this project please also read the [Contribution Guideline](/CONTRIBUTING.md).

> Note: To just run the Sketch Map Tool locally, provide the required [configuration](/docs/configuration.md)
> and use Docker Compose: `docker compose up -d`.

## Prerequisites (Requirements)

- Python: `>= 3.11, < 3.13`
- Poetry
- Node: `>=14`
- NPM
- GDAL
- freetype *(dependency of reportlab for creating PDFs)*
- zbar *(dependency of pyzbar for reading QR-codes)*

This project uses [Poetry](https://python-poetry.org/docs/) and [NPM](https://docs.npmjs.com/) for environment and dependencies management.

```bash
# Mac OS X:
# Make sure to have Python (and pip) and Node (and npm) installed
brew install \
    pipx \
    gdal \
    freetype \
    zbar
pipx install poetry

# Debian/Ubuntu
sudo apt install \
    python3 \
    python3-pip \
    python3-gdal \
    python3-dev \
    pipx \
    nodejs \
    npm \
    libgdal-dev \
    libfreetype6-dev \
    libzbar0
pipx install poetry
```

## Installation

### Python Package

> Then execute steps below. Please see also the section on [Setup in an IDE](#Setup-in-an-IDE).

```bash
# clone repository
git clone https://github.com/GIScience/sketch-map-tool.git
cd sketch-map-tool

poetry install
poetry shell
pip install gdal=="$(gdal-config --version).*"
pre-commit install

# compile languages:
pybabel compile -d sketch_map_tool/translations

npm install
npm run build
```

### Postgres (Database and Result Store) and Redis (Message Broker)

```bash
# fetch and run backend (postgres) and broker (redis) using docker
docker run --name smt-postgres -d -p 5432:5432 -e POSTGRES_PASSWORD=smt -e POSTGRES_USER=smt postgres:15
docker run --name smt-redis -d -p 6379:6379 redis:7
```

## Configuration

Please refer to the [configuration documentation](/docs/configuration.md).

> TL;DR: Except of the API token for arcgis.com (ESRI) all
> configuration values come with defaults for development purposes. Please make
> sure to configure the API tokens for your environment.

## Usage

### 1. Start Celery (Task Queue)

```bash
mamba activate smt
docker start smt-postgres smt-redis
celery --app sketch_map_tool.tasks worker --beat --pool solo --loglevel=INFO
```

### 2. Start Flask (Web App)

```bash
mamba activate smt
pybabel compile -d sketch_map_tool/translations
flask --app sketch_map_tool/routes.py --debug run
# Go to http://127.0.0.1:5000
```

## Back-End

### Linter and Formatter

This tool uses [ruff](https://docs.astral.sh/ruff/) as linter and code formatter. To execute both run:

```bash
ruff check --fix
ruff format
```

### Tests

Provide required [configuration variables](/docs/configuration.md#required-configuration) in `config/test.config.toml`. Be sure *not* to set `broker-url` and `result-backend`.

To execute all tests run:
```bash
pytest
```

To get live logs, INFO log level and ignore verbose logging messages of VCR run:
```bash
pytest --capture=no --log-level="INFO" --log-disable="vcr"
```

The integration test suite utilizes the [Testcontainers framework](https://testcontainers.com/) 
to run unique instances of Redis and Postgres for each test session. It also
configures and starts Flask and Celery workers in the background.

Many fixtures are written to a temporary directory on disk managed by Pytest.
This makes it easy to inspect the results at various steps of the program (E.g.
Marking detection pipeline). Unix users usually find this directory under
`/tmp/pytest-of-{user}/pytest-current/{uuid}/`. The UUID of requests triggered
by the tests (E.g. Create or digitize) is the directory name.

The integration tests will make requests to external services. Among others
requests are made to HeiGIT Maps (WMS) to retrieve basemap images. Those
requests can only be made from HeiGITs internal network.

Some test are using the [Approval Testing methodology](https://approvaltests.com/).
Approval tests capture the output (snapshot) of a piece of code and compare it
with a previously approved version of the output.

Once the output has been *approved* then as long as the output stays the same
the test will pass. A test fails if the *received* output is not identical to
the approved version. In that case, the difference of the received and the
approved output is reported to the tester. The representation of the report can
take any form: A diff-tool comparing received and approved text or images side-by-side.

In the case of the Sketch Map Tool the report takes the form of two images
side-by-side, the uploaded sketch map with markings (input) and the resulting
GeoJSON with the detected markings.

### Stress Tests

[See](/tests/stress/README.md) documentation on how Hurl is used to do stress testing.


### Implementing Exceptions

The use of custom exceptions is highly encouraged.

To translate error messages all custom exceptions should inherit from the `TranslatableError` class (see `exceptions.py`).
A `TranslatableError` should have as first argument a message wrapped in a `N_()` function (see `helper.py`), to mark it for translation, and optionally a dictionary with values for interpolation.

> Note: For more information on translation please see [/docs/translation.md]

## Front-End (HTML, CSS and JS)

For the individual HTML pages the JS and CSS code should be developed in `client-src/**` as 
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

## Database

To connect to the Postgres database when running it as Docker container with the before mentioned Docker run command:
`psql -h localhost -d smt -U smt -p 5432 -W`.

If you run the database as Docker Compose service run:
`psql -h localhost -d smt -U smt -p 5444 -W`.

## Troubleshooting

### NotImplementedError: The operator 'aten::upsample_bicubic2d.out'

If you encounter following error please set the environment variable
`PYTORCH_ENABLE_MPS_FALLBACK=1`.

```bash
NotImplementedError: The operator 'aten::upsample_bicubic2d.out' is not currently implemented for the MPS device. If you want this op to be added in priority during the prototype phase of this feature, please comment on https://github.com/pytorch/pytorch/issues/77764. As a temporary fix, you can set the environment variable `PYTORCH_ENABLE_MPS_FALLBACK=1` to use the CPU as a fallback for this op. WARNING: this will be slower than running natively on MPS.
```
