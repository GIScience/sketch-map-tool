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
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /uvx /bin/

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

ENV UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300s

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project \
    && uv pip install \
        gdal[numpy]=="$(gdal-config --version).*" \
        psycopg2

COPY sketch_map_tool sketch_map_tool
COPY data data
COPY config config

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-editable \
    && uv run pybabel compile -d sketch_map_tool/translations


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
COPY --chown=smt:smt sketch_map_tool sketch_map_tool
COPY --chown=smt:smt data data
COPY --chown=smt:smt config config
COPY --from=node-builder --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles
# use entry-points defined in docker-compose file
