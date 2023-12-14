from geojson import FeatureCollection

from sketch_map_tool.upload_processing import polygonize


def test_polygonize(sketch_map_frame_markings_detected_buffer):
    fc = polygonize(sketch_map_frame_markings_detected_buffer, "red")
    assert fc.is_valid
    assert isinstance(fc, FeatureCollection)
