import json
from io import BytesIO
from uuid import UUID, uuid4

import geojson

# from celery import chain, group
from flask import Response, redirect, render_template, request, send_file, url_for

from sketch_map_tool import celery_app, config, definitions, tasks, upload_processing
from sketch_map_tool import flask_app as app
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import (
    CustomFileNotFoundError,
    MapGenerationError,
    OQTReportError,
    QRCodeError,
    TranslatableError,
    UploadLimitsExceededError,
    UUIDNotFoundError,
)
from sketch_map_tool.helpers import to_array
from sketch_map_tool.models import Bbox, Layer, PaperFormat, Size
from sketch_map_tool.tasks import digitize_sketches, georeference_sketch_maps
from sketch_map_tool.validators import (
    validate_type,
    validate_uploaded_sketchmaps,
    validate_uuid,
)


@app.get("/")
@app.get("/<lang>")
def index(lang="en") -> str:
    return render_template("index.html", lang=lang)


@app.get("/help")
@app.get("/<lang>/help")
def help(lang="en") -> str:
    return render_template("help.html", lang=lang)


@app.get("/about")
@app.get("/<lang>/about")
def about(lang="en") -> str:
    return render_template(
        "about.html", lang=lang, literature=definitions.LITERATURE_REFERENCES
    )


@app.get("/create")
@app.get("/<lang>/create")
def create(lang="en") -> str:
    """Serve forms for creating a sketch map"""
    return render_template(
        "create.html",
        lang=lang,
        esri_api_key=config.get_config_value("esri-api-key"),
    )


@app.post("/create/results")
@app.post("/<lang>/create/results")
def create_results_post(lang="en") -> Response:
    """Create the sketch map"""
    # Request parameters
    bbox_raw = json.loads(request.form["bbox"])
    bbox_wgs84_raw = json.loads(request.form["bboxWGS84"])
    bbox = Bbox(*bbox_raw)
    bbox_wgs84 = Bbox(*bbox_wgs84_raw)
    format_raw = request.form["format"]
    format_: PaperFormat = getattr(definitions, format_raw.upper())
    orientation = request.form["orientation"]
    size_raw = json.loads(request.form["size"])
    size = Size(**size_raw)
    scale = float(request.form["scale"])
    layer = Layer(request.form["layer"].replace(":", "-").replace("_", "-").lower())

    # Unique id for current request
    uuid = str(uuid4())

    # Tasks
    task_sketch_map = tasks.generate_sketch_map.apply_async(
        args=(uuid, bbox, format_, orientation, size, scale, layer)
    )
    task_quality_report = tasks.generate_quality_report.apply_async(args=(bbox_wgs84,))

    # Map of request type to multiple Async Result IDs
    map_ = {
        "sketch-map": str(task_sketch_map.id),
        "quality-report": str(task_quality_report.id),
    }
    db_client_flask.set_async_result_ids(uuid, map_)
    return redirect(url_for("create_results_get", lang=lang, uuid=uuid))


@app.get("/create/results")
@app.get("/<lang>/create/results")
@app.get("/create/results/<uuid>")
@app.get("/<lang>/create/results/<uuid>")
def create_results_get(lang="en", uuid: str | None = None) -> Response | str:
    if uuid is None:
        return redirect(url_for("create", lang=lang))
    validate_uuid(uuid)
    # Check if celery tasks for UUID exists
    _ = db_client_flask.get_async_result_id(uuid, "sketch-map")
    _ = db_client_flask.get_async_result_id(uuid, "quality-report")
    return render_template("create-results.html", lang=lang)


@app.get("/digitize")
@app.get("/<lang>/digitize")
def digitize(lang="en") -> str:
    """Serve a file upload form for sketch map processing"""
    return render_template("digitize.html", lang=lang)


@app.post("/digitize/results")
@app.post("/<lang>/digitize/results")
def digitize_results_post(lang="en") -> Response:
    """Upload files to create geodata results"""
    # No files uploaded
    if "file" not in request.files:
        return redirect(url_for("digitize", lang=lang))
    files = request.files.getlist("file")
    validate_uploaded_sketchmaps(files)
    ids = db_client_flask.insert_files(files)
    file_names = [db_client_flask.select_file_name(i) for i in ids]
    args = [
        upload_processing.read_qr_code(to_array(db_client_flask.select_file(_id)))
        for _id in ids
    ]
    uuids = [args_["uuid"] for args_ in args]
    bboxes = [args_["bbox"] for args_ in args]
    layer_types = [args_["layer"] for args_ in args]

    map_frames = dict()
    for uuid in set(uuids):  # Only retrieve map_frame once per uuid to save memory
        map_frame_buffer = BytesIO(db_client_flask.select_map_frame(UUID(uuid)))
        map_frames[uuid] = to_array(map_frame_buffer.read())
    result_id_1 = (
        georeference_sketch_maps.s(ids, file_names, uuids, map_frames, bboxes)
        .apply_async()
        .id
    )
    result_id_2 = (
        digitize_sketches.s(ids, file_names, uuids, map_frames, layer_types, bboxes)
        .apply_async()
        .id
    )
    # Unique id for current request
    uuid = str(uuid4())
    # Mapping of request id to multiple tasks id's
    map_ = {
        "raster-results": str(result_id_1),
        "vector-results": str(result_id_2),
    }
    db_client_flask.set_async_result_ids(uuid, map_)
    return redirect(url_for("digitize_results_get", lang=lang, uuid=uuid))


@app.get("/digitize/results")
@app.get("/<lang>/digitize/results")
@app.get("/digitize/results/<uuid>")
@app.get("/<lang>/digitize/results/<uuid>")
def digitize_results_get(lang="en", uuid: str | None = None) -> Response | str:
    if uuid is None:
        return redirect(url_for("digitize", lang=lang))
    validate_uuid(uuid)
    return render_template("digitize-results.html", lang=lang)


@app.get("/api/status/<uuid>/<type_>")
@app.get("/<lang>/api/status/<uuid>/<type_>")
def status(uuid: str, type_: REQUEST_TYPES, lang="en") -> Response:
    validate_uuid(uuid)
    validate_type(type_)

    id_ = db_client_flask.get_async_result_id(uuid, type_)
    task = celery_app.AsyncResult(id_)

    href = None
    error = None
    if task.ready():
        if task.successful():  # SUCCESS
            http_status = 200
            href = "/api/download/" + uuid + "/" + type_
        elif task.failed():  # REJECTED, REVOKED, FAILURE
            try:
                task.get(propagate=True)
            except (QRCodeError, OQTReportError, MapGenerationError) as err:
                # The request was well-formed but was unable to be followed due
                # to semantic errors.
                http_status = 422  # Unprocessable Entity
                error = err.translate()
            except Exception as err:
                http_status = 500  # Internal Server Error
                error = repr(err)
    else:  # PENDING, RETRY, STARTED
        # Accepted for processing, but has not been completed
        http_status = 202  # Accepted
    body_raw = {
        "id": uuid,
        "status": task.status,
        "type": type_,
        "href": href,
        "error": error,
    }
    body = {k: v for k, v in body_raw.items() if v is not None}
    return Response(json.dumps(body), status=http_status, mimetype="application/json")


@app.route("/api/download/<uuid>/<type_>")
@app.route("/<lang>/api/download/<uuid>/<type_>")
def download(uuid: str, type_: REQUEST_TYPES, lang="en") -> Response:
    validate_uuid(uuid)
    validate_type(type_)

    id_ = db_client_flask.get_async_result_id(uuid, type_)
    task = celery_app.AsyncResult(id_)

    match type_:
        case "quality-report":
            mimetype = "application/pdf"
            download_name = type_ + ".pdf"
            if task.successful():
                file: BytesIO = task.get()
        case "sketch-map":
            mimetype = "application/pdf"
            download_name = type_ + ".pdf"
            if task.successful():
                file: BytesIO = task.get()
        case "raster-results":
            mimetype = "application/zip"
            download_name = type_ + ".zip"
            if task.successful():
                file = task.get()
        case "vector-results":
            mimetype = "application/geo+json"
            download_name = type_ + ".geojson"
            if task.successful():
                file = BytesIO(geojson.dumps(task.get()).encode("utf-8"))
    return send_file(file, mimetype, download_name=download_name)


@app.route("/api/health")
@app.route("/<lang>/api/health")
def health(lang="en"):
    """Ping Celery workers."""
    result: list = celery_app.control.ping(timeout=1)
    if result:
        return Response(None, status=200)
    return Response(None, status=503)


@app.errorhandler(QRCodeError)
@app.errorhandler(CustomFileNotFoundError)
@app.errorhandler(UploadLimitsExceededError)
def handle_exception(error: TranslatableError):
    return render_template("error.html", error_msg=error.translate()), 422


@app.errorhandler(UUIDNotFoundError)
def handle_not_found_exception(error: TranslatableError):
    return render_template("error.html", error_msg=error.translate()), 404
