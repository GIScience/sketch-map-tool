# build node app
FROM node:16-slim AS node-builder

# install JS dependencies
COPY package.json package.json
COPY esbuild.js esbuild.js
COPY client-src/ client-src/

RUN npm install
RUN mkdir -p /sketch_map_tool/static/bundles
RUN npm run build


# build python app
FROM python:3.12-bookworm AS python-builder

WORKDIR /app

RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y --no-upgrade --no-install-recommends \
        libfreetype6-dev \
        libgdal-dev \
        libpq-dev \
        libzbar0 \
        python3-gdal

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_REQUESTS_TIMEOUT=600

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR python3 -m pip install --break-system-packages poetry setuptools \
    && python3 -m poetry install --only main --no-root --no-directory

COPY sketch_map_tool sketch_map_tool
COPY data data
COPY config config

RUN --mount=type=cache,target=$POETRY_CACHE_DIR python3 -m poetry install --only main --no-root --no-directory \
    && python3 -m poetry run python -m pip install \
        gdal[numpy]=="$(gdal-config --version).*" \
        psycopg2 \
    && python3 -m poetry run pybabel compile -d sketch_map_tool/translations


# final image
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y --no-upgrade --no-install-recommends \
        libgdal32 \
        libzbar0

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=python-builder --chown=smt:smt $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=python-builder --chown=smt:smt /app/sketch_map_tool sketch_map_tool
COPY --from=python-builder --chown=smt:smt /app/data data
COPY --from=python-builder --chown=smt:smt /app/config config
COPY --from=node-builder --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles
# use entry-points defined in docker-compose file
