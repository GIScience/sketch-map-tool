from io import BytesIO
from pathlib import Path
from typing import assert_never
from zipfile import ZipFile

import cv2
import numpy as np
from billiard.exceptions import TimeLimitExceeded
from celery.result import AsyncResult, GroupResult
from geojson import Feature, FeatureCollection, Point
from numpy.typing import NDArray
from reportlab.graphics.shapes import Drawing
from shapely.geometry import shape

from sketch_map_tool.exceptions import TimeLimitExceededError, TranslatableError


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
            properties = f.properties
            features.append(Feature(geometry=f.geometry, properties=properties))
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


def extract_errors(
    async_result: AsyncResult | GroupResult,
    type_,
) -> list[str]:
    """Extract known/custom exceptions propagated by a Celery task or group.

    raises: Re-raises exception if error is not a custom exception.
    """
    if isinstance(async_result, AsyncResult):
        results = [async_result]
    elif isinstance(async_result, GroupResult):
        results = async_result.results
    else:
        assert_never()
    errors = []
    for r in results:  # type: ignore
        if r.ready():
            try:
                r.get(propagate=True)
            except TranslatableError as error:
                errors.append(error.translate())
            except TimeLimitExceeded as error:
                try:
                    raise TimeLimitExceededError(
                        N_(
                            "We couldn’t process your submission because it took too "
                            "long. Please try again later. If the problem persists, "
                            "reach out to us: sketch-map-tool@heigit.org"
                        )
                    ) from error
                except TimeLimitExceededError as error_:
                    errors.append(error_.translate())
            if type_ in ("vector-results"):
                _, _, _, _, errors_ = r.get(propagate=False)
                if len(errors_) > 0:
                    errors = errors + [e.translate() for e in errors_]
    return errors


def extract_centroids(feature_collection: FeatureCollection) -> FeatureCollection:
    centroids = []

    for feature in feature_collection.features:
        geom = shape(feature.geometry)
        centroid_point = Point((geom.centroid.x, geom.centroid.y))
        centroids.append(
            Feature(geometry=centroid_point, properties=feature.properties)
        )

    return FeatureCollection(centroids)
