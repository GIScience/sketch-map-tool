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
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# install system libraries
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
        libgl1 \
        libglib2.0-dev \
        python3-gdal

ENV UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300

# install only gdal build dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev --only-group gdal-build-dependencies

# install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev

COPY sketch_map_tool sketch_map_tool
COPY data data
COPY config config

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-editable --no-dev && \
    uv run pybabel compile -d sketch_map_tool/translations


# final image
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y --no-upgrade --no-install-recommends \
        libgdal32 \
        libzbar0 \
        libgl1 \
        libglib2.0-0

COPY --from=python-builder --chown=smt:smt $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=python-builder --chown=smt:smt /app/sketch_map_tool sketch_map_tool
COPY --from=python-builder --chown=smt:smt /app/data data
COPY --from=python-builder --chown=smt:smt /app/config config
COPY --from=node-builder --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles
# use entry-points defined in docker-compose file
