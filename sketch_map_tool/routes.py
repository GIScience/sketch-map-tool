import json
from pathlib import Path
from typing import Dict, Optional, Union
from uuid import UUID, uuid4

from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

app = Flask(__name__)


@app.get("/")
def index() -> str:
    return render_template("index2.html")


@app.get("/create")
def create() -> str:
    """Serve forms for creating a sketch map"""
    return render_template("create.html")


@app.post("/create/results")
def create_results_post() -> Response:
    """Create the sketch map"""
    bbox = json.loads(request.form["bbox"])
    request.form["format"]
    request.form["orientation"]
    size = json.loads(request.form["size"])
    print(request.form)
    print(size)
    print(bbox)
    uuid = uuid4()
    # return render_template("create-results.html", uuid=str(uuid))
    return redirect(url_for("create_results_get", uuid=uuid))


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


# TODO
# Define status endpoints for creation of sketch maps, quality reports and detection
@app.get("/api/status/<uuid>")
def status(uuid: str) -> Dict[str, str]:
    # TODO validate uuid
    # TODO check task queue of task is finished
    state = "finished"
    if state == "finished":
        return {"id": uuid, "status": "finished"}
    else:
        return {"id": uuid, "status": "computing"}


# TODO
# Define status endpoints for creation of sketch maps, quality reports and detection
@app.route("/api/download")
def download() -> Response:
    return send_from_directory(
        str(Path(__file__).parent / "data"),
        "mock.pdf",
        as_attachment=True,
        mimetype="application/pdf",
    )
