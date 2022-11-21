from sketch_map_tool.models import Bbox
from sketch_map_tool.oqt_analyses.oqt_client import bbox_to_polygon, get_report
from tests import vcr_app as vcr


def test_bbox_to_polygon(bbox_wgs84):
    expected = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[8.625, 49.3711], [8.7334, 49.3711], [8.7334, 49.4397], [8.625, 49.4397], [8.625, 49.3711]]]
        }
    }
    assert expected == bbox_to_polygon(bbox_wgs84)


# todo improve test
@vcr.use_cassette()
def test_get_report(bbox_wgs84):
    report = get_report(bbox_wgs84)
    assert isinstance(report, dict)
