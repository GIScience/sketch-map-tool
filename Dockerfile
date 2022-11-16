FROM python:3.10

# within docker container: run without root privileges
RUN useradd -md /home/smt smt
WORKDIR /opt/smt
RUN chown smt:smt . -R
USER smt:smt

# make poetry binaries available to the docker container user
ENV PATH=$PATH:/home/smt/.local/bin

# install only the dependencies
COPY --chown=smt:smt pyproject.toml pyproject.toml
COPY --chown=smt:smt poetry.lock poetry.lock
RUN pip install --no-cache-dir poetry
RUN python -m poetry install --no-ansi --no-interaction --no-root

# install libzbar (neccessary for pyzbar to read the QR codes)
# to reduce image size, clean up the apt cache by removing /var/lib/apt/lists.
RUN apt-get update && \
    apt-get install -y  libzbar0 && \
    rm -rf /var/lib/apt/lists/*

# copy all the other files and install the project
COPY --chown=smt:smt sketch_map_tool sketch_map_tool
RUN python -m poetry install --no-ansi --no-interaction

WORKDIR /opt/smt

# Use entry-points definied in docker-compose file
