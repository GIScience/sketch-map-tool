FROM python:3.8.13
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
WORKDIR /app/sketch_map_tool
CMD waitress-serve --call app:create_app
