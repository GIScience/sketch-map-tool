import geojson
import pytest
from geojson import FeatureCollection

from sketch_map_tool.upload_processing.post_process import (
    classify_points,
    clean,
    enrich,
)
from tests import FIXTURE_DIR


@pytest.fixture
def markings_with_points():
    path = FIXTURE_DIR / "upload-processing" / "markings-with-points.geojson"
    with open(path, "r") as file:
        fc = geojson.load(file)
    return fc


def test_clean(detected_markings):
    result = clean(detected_markings)
    assert isinstance(result, FeatureCollection)


def test_enrich(detected_markings_cleaned):
    properties = {"name": "sketch-map-1", "color": "1"}
    fc = enrich(detected_markings_cleaned, properties)
    for feature in fc.features:
        assert feature.properties == {"name": "sketch-map-1", "color": "black"}


def test_classify_points(markings_with_points, bbox):
    result = classify_points(markings_with_points, bbox)

    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 5

    number_of_points = 0
    for r, m in zip(result["features"], markings_with_points["features"]):
        assert r.properties == m.properties
        if r.geometry.type == "Point":
            number_of_points = number_of_points + 1
    assert number_of_points == 3


def test_classify_points_no_points(detected_markings, bbox):
    result = classify_points(detected_markings, bbox)

    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 5

    number_of_points = 0
    for r, m in zip(result["features"], detected_markings["features"]):
        assert r.properties == m.properties
        if r.geometry.type == "Point":
            number_of_points = number_of_points + 1
    assert number_of_points == 0
