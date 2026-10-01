# build node app
FROM node:24-trixie-slim AS node-builder

WORKDIR /app
# install JS dependencies
COPY package.json package.json
COPY package-lock.json package-lock.json
COPY esbuild.mjs esbuild.mjs
COPY client-src/ client-src/

RUN npm install
RUN mkdir -p sketch_map_tool/static/bundles
RUN npm run build


# build python app
FROM ubuntu:26.04 AS python-builder
COPY --from=ghcr.io/astral-sh/uv:0.12.20 /uv /uvx /bin/

WORKDIR /app

# install system libraries
RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y --no-upgrade --no-install-recommends \
        build-essential \
        python3-dev \
        git \
        ca-certificates \
        libfreetype6-dev \
        libgdal-dev \
        libpq-dev \
        libzbar0 \
        libgl1 \
        libglib2.0-dev

RUN test "$(gdal-config --version)" = "3.12.2" || (echo "GDAL mismatch: $(gdal-config --version)"; exit 1)

ENV UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300 \
    UV_PYTHON_DOWNLOADS=never

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
FROM ubuntu:26.04 AS runtime

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y --no-upgrade --no-install-recommends \
        python3 \
        ca-certificates \
        libcairo2 \
        libgdal38 \
        libzbar0 \
        libgl1 \
        libglib2.0-0

COPY --from=python-builder --chown=smt:smt $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=python-builder --chown=smt:smt /app/sketch_map_tool sketch_map_tool
COPY --from=python-builder --chown=smt:smt /app/data data
COPY --from=python-builder --chown=smt:smt /app/config config
COPY --from=node-builder --chown=smt:smt /app/sketch_map_tool/static/bundles sketch_map_tool/static/bundles
# use entry-points defined in docker-compose file
