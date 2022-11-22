import json
from io import BytesIO
from typing import get_args
from uuid import uuid4

from celery.states import PENDING, RECEIVED, RETRY, STARTED, SUCCESS
from flask import Response, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from sketch_map_tool import definitions
from sketch_map_tool import flask_app as app
from sketch_map_tool import tasks
from sketch_map_tool.data_store import client as ds_client  # type: ignore
from sketch_map_tool.definitions import ALLOWED_TYPES, DIGITIZE_TYPES
from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.validators import validate_type, validate_uuid


@app.get("/")
def index() -> str:
    return render_template("index2.html")


@app.get("/help")
def help() -> str:
    return render_template("help.html")


@app.get("/about")
def about() -> str:
    return render_template("about.html", literature=definitions.LITERATURE_REFERENCES)


@app.get("/create")
def create() -> str:
    """Serve forms for creating a sketch map"""
    return render_template("create.html")


@app.post("/create/results")
def create_results_post() -> Response:
    """Create the sketch map"""
    # Request parameters
    bbox_raw = json.loads(request.form["bbox"])
    bbox = Bbox(*bbox_raw)
    format_raw = request.form["format"]
    format_: PaperFormat = getattr(definitions, format_raw.upper())
    orientation = request.form["orientation"]
    size_raw = json.loads(request.form["size"])
    size = Size(**size_raw)
    scale = float(request.form["scale"])

    # Tasks
    task_sketch_map = tasks.generate_sketch_map.apply_async(
        args=(bbox, format_, orientation, size, scale)
    )
    task_quality_report = tasks.generate_quality_report.apply_async(args=(bbox,))

    # Unique id for current request
    uuid = str(uuid4())
    # Mapping of request id to multiple tasks id's
    request_task = {
        uuid: json.dumps(
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
def create_results_get(uuid: str | None = None) -> Response | str:
    if uuid is None:
        return redirect(url_for("create"))
    validate_uuid(uuid)
    return render_template("create-results.html")


@app.get("/digitize")
def digitize() -> str:
    """Serve a file upload form for sketch map processing"""
    return render_template("digitize.html")


@app.post("/digitize/results")
def digitize_results_post() -> Response:
    """Upload files to create geodata results"""
    # Request parameters
    # check if the post request has the file part
    if "file" not in request.files:
        # flash('No file part')
        print("No files")
        return redirect(url_for("digitize"))
    files = request.files.getlist("file")
    print(files)
    # TODO FileStorage seems not to be serializable -> Error too much Recursion
    # the map function transforms the list of FileStorage Objects to a list of bytes
    # not sure if this is the best approach but is accepted by celery task
    # if we want the filenames we must construct a list of tuples or dicts
    new_files = list(
        map(
            lambda item: {
                "filename": secure_filename(item.filename),
                "mimetype": item.mimetype,
                "bytes": BytesIO(item.read()),
            },
            files,
        )
    )
    # close the temporary files in the FileStorage objects
    map(lambda item: item.close(), files)

    print(new_files)
    # TODO process the files
    task_digitize = tasks.generate_digitized_results.apply_async(args=(new_files,))

    # Unique id for current request created by celery
    uuid = task_digitize.id

    return redirect(url_for("digitize_results_get", uuid=uuid))


@app.get("/digitize/results")
@app.get("/digitize/results/<uuid>")
def digitize_results_get(uuid: str | None = None) -> Response | str:
    if uuid is None:
        return redirect(url_for("digitize"))
    validate_uuid(uuid)
    return render_template("digitize-results.html")


def get_task_id(uuid: str, type_: str) -> int:
    """Get the celery task id from the data store using the request id and type."""
    if type_ in list(get_args(DIGITIZE_TYPES)):
        # Task id equals request uuid (/digitize/results)
        return uuid
    # Get task id from data-store (/create/results)
    raw = ds_client.get(str(uuid))
    if raw is None:
        raise KeyError("There are no tasks in the broker for UUID: " + uuid)
    request_task = json.loads(raw)
    try:
        task_id = request_task[type_]
    except KeyError as error:
        raise KeyError("There are no tasks in the broker for type: " + type_) from error
    return task_id


@app.get("/api/status/<uuid>/<type_>")
def status(uuid: str, type_: ALLOWED_TYPES) -> Response:
    validate_uuid(uuid)
    validate_type(type_)

    task_id = get_task_id(uuid, type_)

    match type_:
        case "quality-report":
            task = tasks.generate_quality_report.AsyncResult(task_id)
        case "sketch-map":
            task = tasks.generate_sketch_map.AsyncResult(task_id)
        case "digitized-data":
            task = tasks.generate_digitized_results.AsyncResult(task_id)

    # see celery states and their precedence here:
    # https://docs.celeryq.dev/en/stable/_modules/celery/states.html#precedence
    body = {"id": uuid, "status": task.status, "type": type_}
    if task.status == SUCCESS:
        http_status = 200
        body["href"] = "/api/download/" + uuid + "/" + type_
    elif task.status in [PENDING, RETRY, RECEIVED, STARTED]:
        # Accepted for processing, but has not been completed
        http_status = 202  # Accepted
    else:  # Incl. REJECTED, REVOKED, FAILURE
        try:
            task.get(propagate=True)
        except QRCodeError as error:
            # The request was well-formed but was unable to be followed due to semantic
            # errors.
            http_status = 422  # Unprocessable Entity
            body["error"] = str(error)
        else:
            http_status = 500  # Internal Server Error
    return Response(json.dumps(body), status=http_status, mimetype="application/json")


@app.route("/api/download/<uuid>/<type_>")
def download(uuid: str, type_: ALLOWED_TYPES) -> Response:
    validate_uuid(uuid)
    validate_type(type_)

    task_id = get_task_id(uuid, type_)

    match type_:
        case "quality-report":
            task = tasks.generate_quality_report.AsyncResult(task_id)
            mimetype = "application/pdf"
        case "sketch-map":
            task = tasks.generate_sketch_map.AsyncResult(task_id)
            mimetype = "application/pdf"
        case "digitized-data":
            task = tasks.generate_digitized_results.AsyncResult(task_id)
            mimetype = "application/pdf"
            # TODO:
            # mimetype = "application/zip"
    if task.ready():
        file: BytesIO = task.get()
        return send_file(file, mimetype)
