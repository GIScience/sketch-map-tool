from sketch_map_tool.upload_processing import enrich


def test_enrich(detected_markings_cleaned):
    properties = {"name": "sketch-map-1"}
    fc = enrich(detected_markings_cleaned, properties)
    for feature in fc.features:
        assert feature.properties == properties
