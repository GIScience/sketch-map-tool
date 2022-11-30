from io import BytesIO

from sketch_map_tool.upload_processing import polygonize


def test_polygonize(sketch_map_frame_markings_detected_buffer):
    geojson_buffer = polygonize(sketch_map_frame_markings_detected_buffer, "red")
    assert isinstance(geojson_buffer, BytesIO)
