from io import BytesIO

from reportlab.graphics.shapes import Drawing

from sketch_map_tool.models import Bbox
from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.oqt_analyses.generate_pdf import generate_traffic_light, generate_pdf
from tests import vcr_app as vcr


def test_generate_traffic_light():
    actual = generate_traffic_light("green")
    assert isinstance(actual, Drawing)


# todo improve test
@vcr.use_cassette('test_get_report')
def test_generate_pdf(bbox_wgs84):
    report = get_report(bbox_wgs84)
    actual = generate_pdf(report)
    assert isinstance(actual, BytesIO)
