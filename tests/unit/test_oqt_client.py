from sketch_map_tool.oqt_analyses.oqt_client import bbox_to_polygon, get_report
from tests import vcr_app as vcr


def test_bbox_to_polygon():
    bbox = [-121.5, 47.25, -120.4, 47.8]
    expected = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-121.5, 47.25], [-120.4, 47.25], [-120.4, 47.8], [-121.5, 47.8], [-121.5, 47.25]]]
        }
    }
    assert expected == bbox_to_polygon(bbox)


# todo improve test
@vcr.use_cassette()
def test_get_report():
    bbox = [8.625, 49.3711, 8.7334, 49.4397]
    report = get_report(bbox)
    assert isinstance(report, dict)
