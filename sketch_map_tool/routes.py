import json
from io import BytesIO
from pathlib import Path
from uuid import UUID

import geojson
from celery import chord, group
from celery.result import AsyncResult, GroupResult
from flask import (
    abort,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from werkzeug import Response

from sketch_map_tool import celery_app, config, definitions, tasks
from sketch_map_tool import flask_app as app
from sketch_map_tool.database import client_flask as db_client_flask
from sketch_map_tool.definitions import REQUEST_TYPES
from sketch_map_tool.exceptions import (
    CustomFileNotFoundError,
    QRCodeError,
    TranslatableError,
    UploadLimitsExceededError,
    UUIDNotFoundError,
)
from sketch_map_tool.helpers import N_, extract_errors, merge, to_array, zip_
from sketch_map_tool.models import Bbox, Layer, PaperFormat, Size
from sketch_map_tool.tasks import (
    cleanup_blobs,
    upload_processing,
)
from sketch_map_tool.validators import (
    validate_bbox,
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


@app.get("/case-studies/cultural-landmarks")
@app.get("/<lang>/case-studies/cultural-landmarks")
def case_study_cultural_landmarks(lang="en") -> str:
    return render_template("case-study-cultural-landmarks.html", lang=lang)


@app.get("/case-studies/cultural-landmarks-pdf")
@app.get("/<lang>/case-studies/cultural-landmarks-pdf")
def case_study_cultural_landmarks_pdf(lang="en") -> Response:  # pyright: ignore
    dir = Path(config.get_config_value("data-dir")) / "case-studies"
    name = "participatory-mapping-for-cultural-landmarks.pdf"
    return send_from_directory(dir, name, as_attachment=True)


@app.get("/case-studies/timor-leste")
@app.get("/<lang>/case-studies/timor-leste")
def case_study_timor_leste(lang="en") -> str:
    return render_template("case-study-timor-leste.html", lang=lang)


@app.get("/case-studies/timor-leste-pdf")
@app.get("/<lang>/case-studies/timor-leste-pdf")
def case_study_timor_leste_pdf(lang="en") -> Response:  # pyright: ignore
    dir = Path(config.get_config_value("data-dir")) / "case-studies"
    name = "participatory-mapping-in-timor-leste.pdf"
    return send_from_directory(dir, name, as_attachment=True)


@app.get("/weights/SMT-OSM.pt")
@app.get("/<lang>/weights/SMT-OSM.pt")
def weights_smt_osm(lang="en") -> Response:  # pyright: ignore
    dir = Path(config.get_config_value("weights-dir"))
    name = "SMT-OSM.pt"
    return send_from_directory(dir, name, as_attachment=True)


@app.get("/weights/SMT-ESRI.pt")
@app.get("/<lang>/weights/SMT-ESRI.pt")
def weights_smt_esri(lang="en") -> Response:  # pyright: ignore
    dir = Path(config.get_config_value("weights-dir"))
    name = "SMT-ESRI.pt"
    return send_from_directory(dir, name, as_attachment=True)


@app.get("/weights/SMT-CLS.pt")
@app.get("/<lang>/weights/SMT-CLS.pt")
def weights_smt_cls(lang="en") -> Response:  # pyright: ignore
    dir = Path(config.get_config_value("weights-dir"))
    name = "SMT-CLS.pt"
    return send_from_directory(dir, name, as_attachment=True)


@app.get("/create")
@app.get("/<lang>/create")
def create(lang="en") -> str:
    """Serve forms for creating a sketch map"""
    # feature flag for enabling aruco markers
    if request.args.get("aruco") is None:
        aruco = False
    else:
        aruco = True

    return render_template(
        "create.html",
        lang=lang,
        aruco=aruco,
        esri_api_key=config.get_config_value("esri-api-key"),
    )


@app.post("/create/results")
@app.post("/<lang>/create/results")
def create_results_post(lang="en") -> Response:
    """Create the sketch map"""
    # Request parameters
    bbox = Bbox(*json.loads(request.form["bbox"]))
    bbox_wgs84 = Bbox(*json.loads(request.form["bboxWGS84"]))
    format_: PaperFormat = getattr(definitions, request.form["format"].upper())
    orientation = request.form["orientation"]
    size = Size(**(json.loads(request.form["size"])))
    scale = float(request.form["scale"])
    layer = Layer(request.form["layer"].replace(":", "-").replace("_", "-").lower())

    # Feature flag for enabling aruco markers
    if request.args.get("aruco") is None:
        aruco = False
    else:
        aruco = True

    # Tasks
    task_sketch_map = tasks.generate_sketch_map.apply_async(
        args=(bbox, format_, orientation, size, scale, layer, aruco)
    )
    return redirect(
        url_for(
            "create_results_get",
            lang=lang,
            uuid=task_sketch_map.id,
            bbox=bbox_wgs84,
        )
    )


@app.get("/create/results")
@app.get("/<lang>/create/results")
@app.get("/create/results/<uuid>")
@app.get("/<lang>/create/results/<uuid>")
@app.get("/create/results/<uuid>/<bbox>")
@app.get("/<lang>/create/results/<uuid>/<bbox>")
def create_results_get(
    lang="en", uuid: str | None = None, bbox: str = ""
) -> Response | str:
    if uuid is None:
        return redirect(url_for("create", lang=lang))
    if bbox != "":
        validate_bbox(bbox)
    validate_uuid(uuid)
    # Check if celery tasks for UUID exists
    _ = get_async_result(uuid, "sketch-map")
    return render_template("create-results.html", lang=lang, bbox=bbox)


@app.get("/digitize")
@app.get("/<lang>/digitize")
def digitize(lang="en") -> str:
    """Serve a file upload form for sketch map processing"""
    return render_template("digitize.html", lang=lang)


@app.post("/digitize/results")
@app.post("/<lang>/digitize/results")
def digitize_results_post(lang="en") -> Response:
    """Upload files to create geodata results"""
    # user consent to use uploaded files for service improvement
    consent = request.form.get("consent", "False") == "True"
    # No files uploaded
    if "file" not in request.files:
        return redirect(url_for("digitize", lang=lang))
    files = request.files.getlist("file")
    # TODO: move verification to `insert_files()` for incremental validation
    validate_uploaded_sketchmaps(files)
    # file metadata parsed from qr-code
    file_ids, uuids, file_names, bboxes, layers = db_client_flask.insert_files(
        files,
        consent,
    )
    del files

    bboxes_ = dict()
    layers_ = dict()
    map_frames = dict()
    for uuid in set(uuids):  # Only retrieve map_frame once per uuid to save memory
        # NOTE: bbox and layer could be return once per UUID from DB here
        # instead of multiple times from QR code above.
        # But this does not work with legacy map frames (version 2024.04.15),
        # since those attributes are not stored in the DB.
        map_frame = db_client_flask.select_map_frame(UUID(uuid))
        map_frames[uuid] = to_array(BytesIO(map_frame).read())
    for bbox, layer, uuid in zip(bboxes, layers, uuids):
        bboxes_[uuid] = bbox
        layers_[uuid] = layer

    tasks = []
    for file_id, file_name, uuid in zip(file_ids, file_names, uuids):
        tasks.append(
            upload_processing.signature(
                (
                    file_id,
                    file_name,
                    map_frames[uuid],
                    layers_[uuid],
                    bboxes_[uuid],
                )
            )
        )
    chord_ = chord(
        group(tasks),
        cleanup_blobs.signature(
            kwargs={"file_ids": list(set(file_ids))},
            immutable=True,
        ),
    ).apply_async()
    async_group_result = chord_.parent

    # group results have to be saved for them to be able to be restored later
    async_group_result.save()
    db_client_flask.update_files_digitize_uuid(file_ids, async_group_result.id)
    return redirect(
        url_for(
            "digitize_results_get",
            lang=lang,
            uuid=async_group_result.id,
        )
    )


@app.get("/digitize/results")
@app.get("/<lang>/digitize/results")
@app.get("/digitize/results/<uuid>")
@app.get("/<lang>/digitize/results/<uuid>")
def digitize_results_get(lang="en", uuid: str | None = None) -> Response | str:
    if uuid is None:
        return redirect(url_for("digitize", lang=lang))
    validate_uuid(uuid)
    return render_template("digitize-results.html", lang=lang)


def get_async_result(uuid: str, type_: REQUEST_TYPES) -> AsyncResult | GroupResult:
    """Get Celery `AsyncResult` or restore `GroupResult` for given Celery UUID."""
    if type_ == "sketch-map":
        async_result = celery_app.AsyncResult(uuid)
    elif type_ in ("vector-results", "raster-results"):
        async_result = celery_app.GroupResult.restore(uuid)
    else:
        raise TypeError()

    if async_result is None:
        raise UUIDNotFoundError(
            N_("There are no tasks for UUID {UUID}"),
            {"UUID": uuid},
        )
    else:
        return async_result


@app.get("/api/status/<uuid>/<type_>")
@app.get("/<lang>/api/status/<uuid>/<type_>")
def status(uuid: str, type_: REQUEST_TYPES, lang="en") -> Response:
    validate_uuid(uuid)
    validate_type(type_)

    async_result = get_async_result(uuid, type_)

    href = ""
    info = ""
    errors: list = extract_errors(async_result)
    if async_result.ready():
        if async_result.successful():  # SUCCESS
            status = "SUCCESS"
            http_status = 200
            href = "/api/download/" + uuid + "/" + type_
        elif async_result.failed():  # REJECTED, REVOKED, FAILURE
            status = "FAILURE"
            http_status = 422  # Unprocessable Entity
            if isinstance(async_result, GroupResult):
                if any([r.successful() for r in async_result.results]):  # type: ignore
                    status = "SUCCESS"
                    http_status = 200
                    href = "/api/download/" + uuid + "/" + type_
        else:
            abort(500)
    else:  # PENDING, RETRY, STARTED
        # Accepted for processing, but has not been completed
        http_status = 202  # Accepted
        if isinstance(async_result, AsyncResult):
            status = async_result.status
            info = {"current": 0, "total": 1}
        elif isinstance(async_result, GroupResult):
            # `GroupResult` has no `status` attribute
            results = async_result.results
            if any(r.status == "STARTED" or r.ready() for r in results):  # type: ignore
                status = "STARTED"
            else:
                status = "PENDING"
            info = {
                "current": [r.ready() for r in results].count(True),  # type: ignore
                "total": len(async_result.results),  # type: ignore
            }
        else:
            raise TypeError()
    body_raw = {
        "id": uuid,
        "status": status,
        "type": type_,
        "href": href,
        "errors": errors,
        "info": info,
    }
    # remove items which are empty
    body = {k: v for k, v in body_raw.items() if v}
    return Response(json.dumps(body), status=http_status, mimetype="application/json")


@app.route("/api/download/<uuid>/<type_>")
@app.route("/<lang>/api/download/<uuid>/<type_>")
def download(uuid: str, type_: REQUEST_TYPES, lang="en") -> Response:
    validate_uuid(uuid)
    validate_type(type_)

    async_result = get_async_result(uuid, type_)

    # Abort if result not ready or failed.
    # No nice error message here because user should first check /api/status.
    if isinstance(async_result, GroupResult):
        if not async_result.ready() or all([r.failed() for r in async_result.results]):
            abort(500)
    else:
        if not async_result.ready() or async_result.failed():
            abort(500)

    match type_:
        case "sketch-map":
            db_client_flask.update_map_frame_downloaded(uuid)
            mimetype = "application/pdf"
            download_name = type_ + ".pdf"
            file: BytesIO = async_result.get()
        case "raster-results":
            db_client_flask.update_files_download_raster(uuid)
            mimetype = "application/zip"
            download_name = type_ + ".zip"
            if isinstance(async_result, GroupResult):
                results = async_result.get(propagate=False)
                raster_results = [r[:-1] for r in results]
                file: BytesIO = zip_(raster_results)
            else:
                # support legacy results
                file: BytesIO = async_result.get()
        case "vector-results":
            db_client_flask.update_files_download_vector(uuid)
            mimetype = "application/geo+json"
            download_name = type_ + ".geojson"
            if isinstance(async_result, GroupResult):
                results = async_result.get(propagate=False)
                vector_results = [r[-1] for r in results]
                raw = geojson.dumps(merge(vector_results))
                file: BytesIO = BytesIO(raw.encode("utf-8"))
            else:
                # support legacy results
                file = async_result.get()
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
