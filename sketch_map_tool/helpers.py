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
        color = fc.get("name", "foo")
        for f in fc.features:
            properties = f.properties
            properties["color"] = color
            features.append(Feature(geometry=f.geometry, properties=properties))
    feature_collection = FeatureCollection(features=features)
    return feature_collection


def zip_(
    results: tuple[str, BytesIO] | list[tuple[str, BytesIO]],
) -> BytesIO:
    buffer = BytesIO()
    if isinstance(results, tuple):
        results = [results]
    with ZipFile(buffer, "a") as zip_file:
        for file_name, file in results:
            # attribution = get_attribution(layer)
            # attribution = attribution.replace("<br />", "\n")
            name = ".".join(file_name.split(".")[:-1])
            zip_file.writestr(f"{name}.geotiff", file.read())
        # zip_file.writestr("attributions.txt", get_attribution_file().read())
    buffer.seek(0)
    return buffer
