from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np
from geojson import Feature, FeatureCollection
from numpy.typing import NDArray
from reportlab.graphics.shapes import Drawing


def get_project_root() -> Path:
    """Get root of the Python project."""
    return Path(__file__).resolve().parent.parent.resolve()


def resize_rlg_by_width(d: Drawing, size: float) -> Drawing:
    factor = size / d.width
    d.scale(factor, factor)
    d.asDrawing(d.width * factor, d.height * factor)
    return d


def resize_rlg_by_height(d: Drawing, size: float) -> Drawing:
    factor = size / d.height
    d.scale(factor, factor)
    d.asDrawing(d.width * factor, d.height * factor)
    return d


def to_array(buffer: bytes) -> NDArray:
    return cv2.imdecode(np.frombuffer(buffer, dtype="uint8"), cv2.IMREAD_UNCHANGED)


def N_(s: str) -> str:  # noqa
    """Mark for translation."""
    return s


def merge(fcs: list[FeatureCollection]) -> FeatureCollection:
    """Merge multiple GeoJSON Feature Collections."""
    # f   -> feature
    # fc  -> feature collection
    # fcs -> feature collections (multiple)
    features = []
    for fc in fcs:
        for f in fc.features:
            features.append(Feature(geometry=f.geometry, properties=f.properties))
    feature_collection = FeatureCollection(features=features)
    return feature_collection


def zip_(results: list[tuple[str, str, BytesIO]]) -> BytesIO:
    """ZIP the raster results of the Celery group of `upload_processing` tasks."""
    buffer = BytesIO()
    attributions = []
    with ZipFile(buffer, "a") as zip_file:
        for file_name, attribution, file in results:
            stem = Path(file_name).stem
            name = Path(stem).with_suffix(".geotiff")
            zip_file.writestr(str(name), file.read())
            attributions.append(attribution.replace("<br />", "\n"))
        file = BytesIO("\n".join(set(attributions)).encode())
        zip_file.writestr("attributions.txt", file.read())
    buffer.seek(0)
    return buffer


def transform_layer_name(layer: str) -> str:
    if layer.startswith("osm"):
        return "OSM"
    elif layer.startswith("esri"):
        return "ESRI:World_Imagery"
    return layer
