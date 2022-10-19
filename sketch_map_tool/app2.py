import json
from typing import Dict, Optional, Union
from uuid import UUID, uuid4

from flask import Flask, Response, redirect, render_template, request, url_for

app = Flask(__name__)


@app.get("/")
def index() -> str:
    return render_template("index2.html")


@app.get("/create")
def create() -> str:
    """Serve forms for creating a sketch map"""
    return render_template("create.html")


@app.post("/create/results")
def create_results_post() -> str:
    """Create the sketch map"""
    request.form["bbox"]
    request.form["format"]
    request.form["orientation"]
    size = json.loads(request.form["size"])
    print(request.form)
    print(size)
    uuid = uuid4()
    return render_template("create-results.html", uuid=str(uuid))


@app.get("/create/results")
@app.get("/create/results/<uuid>")
def create_results_get(uuid: Optional[str] = None) -> Union[Response, str]:
    if uuid is None:
        return redirect(url_for("create"))

    # TODO: validate uuid and notify use
    try:
        _ = UUID(uuid, version=4)
    except ValueError:
        raise
    return render_template("create-results.html")


@app.get("/create/results/status/<uuid>")
def create_results_status(uuid: str) -> Dict[str, Union[str, float]]:
    return {"id": uuid, "status": "computing", "progress": 0.5}
