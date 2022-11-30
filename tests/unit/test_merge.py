from geojson import FeatureCollection

from sketch_map_tool.upload_processing import merge


def test_merge(detected_markings_cleaned):
    fc = merge([detected_markings_cleaned, detected_markings_cleaned])
    assert isinstance(fc, FeatureCollection)
    assert len(fc.features) == len(detected_markings_cleaned.features) * 2
