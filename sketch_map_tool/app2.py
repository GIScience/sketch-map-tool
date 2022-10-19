import json
from uuid import UUID, uuid4

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index2.html")


@app.get("/create")
def create():
    """Serve forms for creating a sketch map"""
    return render_template("create.html")


@app.post("/create/results")
def create_results_post():
    """Create the sketch map"""
    request.form["bbox"]
    request.form["format"]
    request.form["orientation"]
    size = json.loads(request.form["size"])
    print(request.form)
    print(size)
    uuid = uuid4()
    return render_template("create-results.html", uuid=uuid)


@app.get("/create/results")
@app.get("/create/results/<uuid>")
def create_results_get(uuid=None):
    if uuid is None:
        return redirect(url_for("create"))

    try:
        uuid = UUID(uuid, version=4)
    except ValueError:
        raise
    return render_template("create-results.html")


@app.get("/create/results/status/<uuid>")
def create_results_status(uuid):
    return {"id": uuid, "status": "computing", "progress": 0.5}
