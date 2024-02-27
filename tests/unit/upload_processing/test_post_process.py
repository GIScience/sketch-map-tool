from geojson import FeatureCollection

from sketch_map_tool.upload_processing.post_process import clean, enrich


def test_clean(detected_markings):
    result = clean(detected_markings)
    assert isinstance(result, FeatureCollection)


def test_enrich(detected_markings_cleaned):
    properties = {"name": "sketch-map-1", "color": "1"}
    fc = enrich(detected_markings_cleaned, properties)
    for feature in fc.features:
        assert feature.properties == {"name": "sketch-map-1", "color": "black"}
