from io import BytesIO

from sketch_map_tool.upload_processing import geopackage


def test_geopackage(detected_markings_cleaned):
    result = geopackage([detected_markings_cleaned, detected_markings_cleaned])
    assert isinstance(result, BytesIO)
