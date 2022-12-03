from io import BytesIO

from reportlab.graphics.shapes import Drawing

from sketch_map_tool.oqt_analyses import get_report
from sketch_map_tool.oqt_analyses.generate_pdf import (
    generate_pdf,
    generate_traffic_light,
)
from tests import vcr_app as vcr
from tests.unit.helper import save_test_file


def test_generate_traffic_light():
    actual = generate_traffic_light("green")
    assert isinstance(actual, Drawing)


# todo improve test
@vcr.use_cassette("test_get_report")
def test_generate_pdf(bbox_wgs84, request):
    report = get_report(bbox_wgs84)
    actual = generate_pdf(report)
    assert isinstance(actual, BytesIO)
    # if you want the report to be saved for visual inspection, use the parameter --save-report with pytest
    save_test_file(request, "--save-report", "report.pdf", actual)
