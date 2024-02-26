FROM node:16-slim AS bundler

# install JS dependencies
COPY package.json package.json
COPY esbuild.js esbuild.js
COPY client-src/ client-src/
RUN npm install
RUN mkdir -p /sketch_map_tool/static/bundles
RUN npm run build


FROM condaforge/mambaforge:latest


RUN apt-get update \
    && apt-get install -y --no-upgrade \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*
        # libzbar0 \
        # libgdal-dev \
# within docker container: run without root privileges
RUN useradd -md /home/smt smt
WORKDIR /opt/smt
RUN chown smt:smt . -R
USER smt:smt

COPY --chown=smt:smt environment.yml environment.yml
RUN mamba env create --file environment.yml

# make RUN commands use the new environment:
SHELL ["mamba", "run", "--no-capture-output", "--name", "smt", "/bin/bash", "-c"]

COPY --chown=smt:smt pyproject.toml pyproject.toml
COPY --chown=smt:smt poetry.lock poetry.lock
RUN which python
RUN python -m poetry install --no-ansi --no-interaction --no-root

COPY --chown=smt:smt sketch_map_tool sketch_map_tool
COPY --chown=smt:smt data/ data/
RUN python -m poetry install --no-ansi --no-interaction

# Compile translations
RUN python3 -m poetry run pybabel compile -d sketch_map_tool/translations

# get JS dependencies
COPY --from=bundler --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles

# use entry-points defined in docker-compose file
