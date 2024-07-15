# Development Setup

For contributing to this project please also read the [Contribution Guideline](/CONTRIBUTING.md).

> Note: To just run the Sketch Map Tool locally, provide the required [configuration](/docs/configuration.md)
> and use Docker Compose: `docker compose up -d`

## Prerequisites (Requirements)

- Python: `>=3.10`
- [Mamba](https://github.com/conda-forge/miniforge#install): `>=1.4`
- Node: `>=14`

This project uses [Mamba](https://github.com/conda-forge/miniforge#install) for environment and dependencies management. Please make sure it is installed on your system: [Installation Guide](https://github.com/conda-forge/miniforge#install). Instead of Mamba, Conda can also be used.

> Actually, Mamba and Poetry together are used to manage environment and dependencies. 
> But only Mamba is required to be present on the system.
> Poetry will be installed by Mamba.
> Mamba installs pre-built binaries for dependencies like GDAL. 
> Poetry installs the rest of the Python dependencies.

## Installation

### Python Package

> Note: Editors like Visual Studio Code or PyCharm (IDEA) will try to automatically setup Sketch Map Tool.
> They will fail if they try to create a virtual environment managed by Poetry.
> If this happens remove the environment (`poetry env remove 3.10`).
> Then execute steps below. Please see also the section on [Project Setup using and IDE](#Project-Setup-using-and-IDE).

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

Note: When dependencies changed the environment can be updated by running:

```bash
mamba activate smt
mamba env update --file environment.yml
poetry install
```

## Configuration

Please refer to the [configuration documentation](/docs/configuration.md).

> TL;DR: Except of the API tokens for neptune.ai and arcgis.com (ESRI) all
> configuration values come with defaults for development purposes. Please make
> sure to configure the API tokens for your environment.

## Usage

### 1. Start Celery (Task Queue)

```bash
mamba activate smt
docker start smt-postgres smt-redis
celery --app sketch_map_tool.tasks worker --beat --concurrency 4 --loglevel=INFO
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

Provide required [configuration variables](/docs/configuration.md#required-configuration) in `config/test.config.toml`.

To execute all tests run:
```bash
pytest
```

To get live logs, INFO log level and ignore verbose logging messages of VCR run:
```bash
pytest -s --log-level="INFO" --log-disable="vcr"
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

## Project Setup using and IDE

If you setup sketch-map-tool in an IDE like PyCharm please make sure that your IDE does not setup a Poetry managed project/virtual environment.
Go thought the setup steps above in the terminal and change interpreter settings in the IDE to point to the mamba/conda environment.

Also make sure the environment variable `PROJ_LIB` to point to the `proj` directory of the mamba/conda environment:
```bash
PROJ_LIB=/home/$USERDIR/mambaforge/envs/smt/share/proj
```

## Troubleshooting

Make sure that Poetry does not try to manage the virtual environment. Check with `poetry env list`. If any environment are listed remove them: `poetry env remove ...`
