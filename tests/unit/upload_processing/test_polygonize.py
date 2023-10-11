from io import BytesIO

import geojson

from sketch_map_tool.upload_processing import polygonize


def test_polygonize(sketch_map_frame_markings_detected_buffer):
    geojson_buffer = polygonize(sketch_map_frame_markings_detected_buffer, "red")
    json = geojson.loads(geojson_buffer.read())
    assert json.is_valid
    assert isinstance(geojson_buffer, BytesIO)
