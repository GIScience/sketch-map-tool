import json
from io import BytesIO
from typing import Optional, Union
from uuid import UUID, uuid4

from celery.states import PENDING, RECEIVED, RETRY, STARTED, SUCCESS
from flask import Response, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from sketch_map_tool import flask_app as app
from sketch_map_tool import tasks
from sketch_map_tool.data_store import client as ds_client  # type: ignore
from sketch_map_tool.models import Bbox, Size

CREATE_TYPES = ["quality-report", "sketch-map"]
DIGITIZE_TYPES = ["digitized-data"]


def validate_result_types(type_):
    """validaton function for endpoint parameter result <type_>"""
    allowed_types = CREATE_TYPES + DIGITIZE_TYPES

    if type_ not in allowed_types:
        raise NameError(
            type_
            + " is not a valid download type. Allowed values are: "
            + allowed_types
        )
    pass


def validate_uuid(uuid: str):
    """validation function for endpoint parameter <uuid>"""
    try:
        _ = UUID(uuid, version=4)
    except ValueError as error:
        raise error


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
    bbox_raw = json.loads(request.form["bbox"])
    bbox = Bbox(*bbox_raw)
    format_ = request.form["format"]
    orientation = request.form["orientation"]
    size_raw = json.loads(request.form["size"])
    size = Size(**size_raw)
    scale = request.form["scale"]

    # Tasks
    task_sketch_map = tasks.generate_sketch_map.apply_async(
        args=(bbox, format_, orientation, size, scale)
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

    try:
        validate_uuid(uuid)
    except ValueError:
        # TODO: notify user in an error template page
        raise "The provided URL does not contain a valid UUID"

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
def digitize_results_get(uuid: Optional[str] = None) -> Union[Response, str]:
    if uuid is None:
        return redirect(url_for("digitize"))

    try:
        validate_uuid(uuid)
    except ValueError:
        # TODO: notify user in an error template page
        raise "The provided URL does not contain a valid UUID"

    return render_template("digitize-results.html")


@app.get("/api/status/<uuid>/<type_>")
def status(uuid: str, type_: CREATE_TYPES + DIGITIZE_TYPES) -> Response:
    try:
        validate_uuid(uuid)
    except ValueError:
        # TODO: notify user in an error template page
        raise "The provided URL does not contain a valid UUID"

    try:
        validate_result_types(type_)
    except NameError as error:
        # TODO: notify user in an error template page
        raise error

    task_id = get_task_id(uuid, type_)

    # TODO: Factor out to own function (tasks module)
    if type_ == "quality-report":
        task = tasks.generate_quality_report.AsyncResult(task_id)
    elif type_ == "sketch-map":
        task = tasks.generate_sketch_map.AsyncResult(task_id)
    elif type_ == "digitized-data":
        task = tasks.generate_digitized_results.AsyncResult(task_id)
    else:
        # Unreachable
        raise ValueError

    # see celery states and their precedence here:
    # https://docs.celeryq.dev/en/stable/_modules/celery/states.html#precedence
    body = {"id": uuid, "status": task.status, "type": type_}
    if task.status == SUCCESS:
        http_status = 200
        body["href"] = "/api/download/" + uuid + "/" + type_
    elif task.status in [PENDING, RETRY, RECEIVED, STARTED]:
        http_status = 202
    else:  # Incl. REJECTED, REVOKED, FAILURE
        http_status = 500
    return Response(json.dumps(body), status=http_status, mimetype="application/json")


def get_task_id(uuid, type_):
    # get task-id
    # either from datastore (/create/results)
    # or directly use uuid from celery (/digitize/results)
    if type_ in CREATE_TYPES:
        task_id = get_create_result_task_id(uuid, type_)
    else:
        task_id = get_digitize_result_task_id(uuid, type_)
    return task_id


def get_create_result_task_id(uuid, type_):
    """Get celery task id from the sketchmap data store"""

    # Map request id and type to tasks id
    raw = ds_client.get(str(uuid))
    if raw is None:
        raise KeyError("There are no entries in the database for UUID: " + str(uuid))
    request_task = json.loads(raw)
    # TODO: Factor out to own function (data store module)
    try:
        task_id = request_task[type_]
        return task_id
    except KeyError as error:
        raise KeyError("Type has to one of " + "string".join(CREATE_TYPES)) from error


def get_digitize_result_task_id(uuid, type_):
    return uuid


@app.route("/api/download/<uuid>/<type_>")
def download(uuid: str, type_: CREATE_TYPES + DIGITIZE_TYPES) -> Response:

    # TODO catch and notify user in error template
    validate_uuid(uuid)
    validate_result_types(type_)

    # get task-id
    # either from datastore (/create/results)
    # or directly use uuid from celery (/digitize/results)
    if type_ in CREATE_TYPES:
        task_id = get_create_result_task_id(uuid, type_)
    else:
        task_id = get_digitize_result_task_id(uuid, type_)

    # TODO: Factor out to own function (tasks module)
    mimetype = "application/pdf"
    if type_ == "quality-report":
        task = tasks.generate_quality_report.AsyncResult(task_id)
        mimetype = ""
    elif type_ == "sketch-map":
        task = tasks.generate_sketch_map.AsyncResult(task_id)
        mimetype = "image/png"
    elif type_ == "digitized-data":
        task = tasks.generate_digitized_results.AsyncResult(task_id)
        # TODO will be zip in the future, but now pdf for testing
        # mimetype = "application/zip"
    else:
        # Unreachable
        pass
    if task.ready():
        pdf: BytesIO = task.get()
        return send_file(
            pdf,
            # mimetype="application/pdf",
            mimetype,
        )
    else:
        # TODO
        pass
