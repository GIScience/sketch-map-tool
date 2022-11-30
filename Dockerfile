FROM node:16-slim AS bundler

# install JS dependencies
COPY package.json package.json
COPY esbuild.js esbuild.js
COPY client-src/ client-src/
RUN npm install
RUN mkdir -p /sketch_map_tool/static/bundles
RUN npm run build


FROM ubuntu:22.04

# install libzbar (neccessary for pyzbar to read the QR codes)
# install gdal
# install libgl1 (for openCV)
# to reduce image size, clean up the apt cache by removing /var/lib/apt/lists.
RUN apt-get update \
    && apt-get install -y --no-upgrade \
        python3-pip \
        libzbar0 \
        libgdal-dev \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

# update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# within docker container: run without root privileges
RUN useradd -md /home/smt smt
WORKDIR /opt/smt
RUN chown smt:smt . -R
USER smt:smt

# make poetry binaries available to the docker container user
ENV PATH=$PATH:/home/smt/.local/bin

COPY --chown=smt:smt pyproject.toml pyproject.toml
COPY --chown=smt:smt poetry.lock poetry.lock
COPY --chown=smt:smt setup.cfg setup.cfg
# install Python dependencies
RUN pip3 install --no-cache-dir poetry
# these versions have to be fixed for now, since poetry and (py)gdal packages can't work together
RUN python3 -m poetry run pip install numpy==1.23.5
RUN python3 -m poetry run pip install pygdal==3.4.1.10
RUN python3 -m poetry install --no-ansi --no-interaction --no-root

# copy all the other files and install the project
COPY --chown=smt:smt sketch_map_tool sketch_map_tool
COPY --chown=smt:smt data/ data/
COPY --chown=smt:smt tests/ tests/
RUN python3 -m poetry install --no-ansi --no-interaction

# get JS dependencies
COPY --from=bundler --chown=smt:smt /sketch_map_tool/static/bundles sketch_map_tool/static/bundles

# Use entry-points defined in docker-compose file
