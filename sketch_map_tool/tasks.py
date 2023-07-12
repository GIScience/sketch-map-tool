from io import BytesIO
from typing import List, Tuple
from uuid import UUID
from zipfile import ZipFile

import geojson
from celery.result import AsyncResult
from celery.signals import worker_process_init, worker_process_shutdown
from geojson import FeatureCollection
from numpy.typing import NDArray
from tempfile import NamedTemporaryFile

from sketch_map_tool import celery_app as celery
from sketch_map_tool import map_generation
from sketch_map_tool.database import client_celery as db_client_celery
from sketch_map_tool.definitions import COLORS
from sketch_map_tool.helpers import to_array
from sketch_map_tool.models import Bbox, PaperFormat, Size
from sketch_map_tool.oqt_analyses import generate_pdf as generate_report_pdf
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.upload_processing import (
    clean,
    clip,
    detect_markings,
    enrich,
    georeference,
    merge,
    polygonize,
    prepare_img_for_markings,
    create_qgis_project,
    generate_heatmap,
)
from sketch_map_tool.wms import client as wms_client


@worker_process_init.connect
def init_worker(**kwargs):
    """Initializing database connection for worker"""
    db_client_celery.open_connection()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    """Closing database connection for worker"""
    db_client_celery.close_connection()


# 1. GENERATE SKETCH MAP & QUALITY REPORT
#
@celery.task()
def generate_sketch_map(
    uuid: UUID,
    bbox: Bbox,
    format_: PaperFormat,
    orientation: str,
    size: Size,
    scale: float,
) -> BytesIO | AsyncResult:
    """Generate and returns a sketch map as PDF and stores the map frame in DB."""
    raw = wms_client.get_map_image(bbox, size)
    map_image = wms_client.as_image(raw)
    qr_code_ = map_generation.qr_code(
        str(uuid),
        bbox,
        format_,
    )
    map_pdf, map_img = map_generation.generate_pdf(
        map_image,
        qr_code_,
        format_,
        scale,
    )
    db_client_celery.insert_map_frame(map_img, uuid)
    return map_pdf


@celery.task()
def generate_quality_report(bbox: Bbox) -> BytesIO | AsyncResult:
    """Generate a quality report as PDF.

    Fetch quality indicators from the OQT API
    """
    report = get_report(bbox)
    return generate_report_pdf(report)


# 2. DIGITIZE RESULTS
# TODO: Avoid duplication in the three tasks, instead let the later ones wait for the first to finish to directly
#       use intermediary results

@celery.task()
def georeference_sketch_maps(
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    bboxes: list[Bbox],
) -> AsyncResult | BytesIO:
    def process(sketch_map_id: int, uuid: str, bbox: Bbox) -> BytesIO:
        """Process a Sketch Map.

        :param sketch_map_id: ID under which the uploaded file is stored in the database.
        :param uuid: UUID under which the sketch map was created.
        :bbox: Bounding box of the AOI on the sketch map.
        :return: Georeferenced image (GeoTIFF) of the sketch map .
        """
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = to_array(r)
        r = clip(r, map_frames[uuid])
        r = georeference(r, bbox)
        return r

    def zip_(files: list, file_names: list[str]) -> BytesIO:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zip_file:
            for upload_name, file in zip(file_names, files):
                name = ".".join(upload_name.split(".")[:-1])
                zip_file.writestr(f"{name}.geotiff", file.read())
        buffer.seek(0)
        return buffer

    return zip_(
        [
            process(file_id, uuid, bbox)
            for file_id, uuid, bbox in zip(file_ids, uuids, bboxes)
        ],
        file_names,
    )


@celery.task()
def digitize_sketches(
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    bboxes: list[Bbox],
) -> AsyncResult | FeatureCollection:
    def process(
        sketch_map_id: int, name: str, uuid: str, bbox: Bbox
    ) -> FeatureCollection:
        """Process a Sketch Map."""
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = to_array(r)
        r = clip(r, map_frames[uuid])
        r = prepare_img_for_markings(map_frames[uuid], r)
        geojsons = []
        for color in COLORS:
            r_ = detect_markings(r, color)
            r_ = georeference(r_, bbox)
            r_ = polygonize(r_, color)
            r_ = geojson.load(r_)
            r_ = clean(r_)
            r_ = enrich(r_, {"color": color, "name": name})
            geojsons.append(r_)
        return merge(geojsons)

    return merge(
        [
            process(file_id, name, uuid, bbox)
            for file_id, name, uuid, bbox in zip(file_ids, file_names, uuids, bboxes)
        ]
    )


@celery.task()
def analyse_markings(
    file_ids: list[int],
    file_names: list[str],
    uuids: list[str],
    map_frames: dict[str, NDArray],
    bboxes: list[Bbox],
    map_frame_template: BytesIO
) -> AsyncResult | FeatureCollection:
    if len(set(bboxes)) != 1:
        raise ValueError("Because the map frame is used as background for the heatmap, this process only works "
                         "when uploading sketch maps covering exactly the same area.")

    def process(
        sketch_map_id: int, name: str, uuid: str, bbox: Bbox
    ) -> FeatureCollection:
        """Process a Sketch Map."""
        # r = interim result
        r = db_client_celery.select_file(sketch_map_id)
        r = to_array(r)
        r = clip(r, map_frames[uuid])
        r = prepare_img_for_markings(map_frames[uuid], r)
        geojsons = []
        for color in COLORS:
            r_ = detect_markings(r, color)
            r_ = georeference(r_, bbox)
            r_ = polygonize(r_, color)
            r_ = geojson.load(r_)
            r_ = clean(r_)
            r_ = enrich(r_, {"color": color, "name": name})
            geojsons.append(r_)
        return merge(geojsons)

    def zip_(qgis_project: BytesIO, heatmaps: List[Tuple[str, BytesIO]]) -> BytesIO:
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zip_file:
            zip_file.writestr(f"qgis_project.zip", qgis_project.read())
            for colour, heatmap in heatmaps:
                zip_file.writestr(f"heatmap_{colour}.jpg", heatmap.read())
        buffer.seek(0)
        return buffer

    qgis_project, overlaps = create_qgis_project(BytesIO(geojson.dumps(merge(
        [
            process(file_id, name, uuid, bbox)
            for file_id, name, uuid, bbox in zip(file_ids, file_names, uuids, bboxes)
        ]
    )).encode("utf-8")))
    geojson_overlaps_file = NamedTemporaryFile(suffix=".geojson")
    map_frame_template_file = NamedTemporaryFile(suffix=".jpg")
    with open(geojson_overlaps_file.name, "wb") as fw:
        fw.write(overlaps.read())
    with open(map_frame_template_file.name, "wb") as fw:
        fw.write(map_frame_template.read())
    return zip_(qgis_project, generate_heatmap(
        geojson_overlaps_file.name,
        bboxes[0].lon_min,
        bboxes[0].lat_min,
        bboxes[0].lon_max,
        bboxes[0].lat_max,
        map_frame_template_file.name))
