import json
from io import BytesIO
from typing import Dict, Literal, Optional, Union
from uuid import UUID, uuid4

from flask import Response, redirect, render_template, request, send_file, url_for

from sketch_map_tool import flask_app as app
from sketch_map_tool import tasks
from sketch_map_tool.data_store import client as ds_client  # type: ignore


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
    # Request parameters
    bbox = json.loads(request.form["bbox"])
    format_ = request.form["format"]
    orientation = request.form["orientation"]
    size = json.loads(request.form["size"])

    # Tasks
    task_sketch_map = tasks.generate_sketch_map.apply_async(
        args=(bbox, format_, orientation, size)
    )
    task_quality_report = tasks.generate_quality_report.apply_async(args=(bbox,))

    # Unique id for current request
    uuid = uuid4()

    # Mapping of request id to multiple tasks id's
    request_task = {
        str(uuid): json.dumps(
            {
                "sketch-map": str(task_sketch_map.id),
                "quality-report": str(task_quality_report.id),
            }
        )
    }
    ds_client.set(request_task)
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


@app.get("/api/status/<uuid>/<type_>")
def status(uuid: str, type_: Literal["quality-report", "sketch-map"]) -> Dict[str, str]:
    """Get the status of a request by uuid and type."""
    # Map request id and type to tasks id
    raw = ds_client.get(str(uuid))
    request_task = json.loads(raw)
    # TODO: Factor out to own function (data store module)
    try:
        task_id = request_task[type_]
    except KeyError as error:
        raise KeyError("Type has to be either quality-report or sketch-map") from error

    # TODO: Factor out to own function (tasks module)
    if type_ == "quality-report":
        task = tasks.generate_quality_report.AsyncResult(task_id)
    elif type_ == "sketch-map":
        task = tasks.generate_sketch_map.AsyncResult(task_id)
    else:
        # Unreachable
        pass

    return {"id": uuid, "status": task.status}


@app.route("/api/download/<uuid>/<type_>")
def download(uuid: str, type_: Literal["quality-report", "sketch-map"]) -> Response:
    # Map request id and type to tasks id
    raw = ds_client.get(str(uuid))
    request_task = json.loads(raw)
    # TODO: Factor out to own function (data store module)
    try:
        task_id = request_task[type_]
    except KeyError as error:
        raise KeyError("Type has to be either quality-report or sketch-map") from error

    # TODO: Factor out to own function (tasks module)
    if type_ == "quality-report":
        task = tasks.generate_quality_report.AsyncResult(task_id)
    elif type_ == "sketch-map":
        task = tasks.generate_sketch_map.AsyncResult(task_id)
    else:
        # Unreachable
        pass
    if task.ready():
        pdf: BytesIO = task.get()
        return send_file(
            pdf,
            mimetype="application/pdf",
        )
    else:
        # TODO
        pass
