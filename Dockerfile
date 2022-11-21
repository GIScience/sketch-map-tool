FROM node:16-slim AS bundler

# install JS dependencies
COPY package.json package.json
COPY esbuild.js esbuild.js
COPY client-src/ client-src/
RUN npm install
RUN mkdir -p /sketch_map_tool/static/bundles
RUN npm run build


FROM python:3.10

# install libzbar (neccessary for pyzbar to read the QR codes)
# to reduce image size, clean up the apt cache by removing /var/lib/apt/lists.
RUN apt-get update && \
    apt-get install -y  libzbar0 && \
    rm -rf /var/lib/apt/lists/*

# within docker container: run without root privileges
RUN useradd -md /home/smt smt
WORKDIR /opt/smt
RUN chown smt:smt . -R
USER smt:smt

# make poetry binaries available to the docker container user
ENV PATH=$PATH:/home/smt/.local/bin

# install Python dependencies
COPY --chown=smt:smt pyproject.toml pyproject.toml
COPY --chown=smt:smt poetry.lock poetry.lock
RUN pip install --no-cache-dir poetry
RUN python -m poetry install --no-ansi --no-interaction --no-root

# copy all the other files and install the project
COPY --chown=smt:smt sketch_map_tool sketch_map_tool
COPY --chown=smt:smt data/ data/
RUN python -m poetry install --no-ansi --no-interaction

# get JS dependencies
COPY --from=bundler --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles

# Use entry-points definied in docker-compose file
