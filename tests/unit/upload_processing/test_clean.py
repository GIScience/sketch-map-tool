from io import BytesIO

from sketch_map_tool.upload_processing import clean


def test_clean(detected_markings):
    result = clean(detected_markings)
    assert isinstance(result, BytesIO)
