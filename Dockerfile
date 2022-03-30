FROM python:3.8.13
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD waitress-serve --call app:create_app
