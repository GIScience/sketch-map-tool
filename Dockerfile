FROM node:16-slim AS bundler

# install JS dependencies
COPY package.json package.json
COPY esbuild.js esbuild.js
COPY client-src/ client-src/

RUN npm install
RUN mkdir -p /sketch_map_tool/static/bundles
RUN npm run build


FROM ubuntu:24.04

RUN apt update \
    && apt install -y --no-upgrade \
    python3 \
    python3-pip \
    python3-numpy \
    python3-gdal \
    python3-psycopg2 \
    git \
    libgdal-dev \
    libpq-dev \
    libzbar0 \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_REQUESTS_TIMEOUT=600

COPY pyproject.toml poetry.lock .

RUN python3 -m pip install --break-system-packages poetry setuptools \
    && python3 -m poetry install --only main --no-root --no-directory

COPY sketch_map_tool sketch_map_tool
COPY data data
COPY config config

RUN python3 -m poetry install --only main --no-root --no-directory \
    && python3 -m poetry run python -m pip install gdal[numpy]=="$(gdal-config --version).*" \
    && python3 -m poetry run pybabel compile -d sketch_map_tool/translations \
    && rm -rf $POETRY_CACHE_DIR

COPY --from=bundler --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles
# use entry-points defined in docker-compose file
