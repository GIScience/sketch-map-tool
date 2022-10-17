"""
Tests for the module printer/generate_sketchmap.py
"""
import os
from unittest.mock import patch

import pytest
from modules.test_get_map import DummyResponse

from sketch_map_tool.constants import (
    GENERATION_OUTPUT_LINK,
    TIMEOUT_REQUESTS,
    WMS_BASE_URL,
    WMS_LAYERS,
)
from sketch_map_tool.helper_modules.bbox_utils import Bbox
from sketch_map_tool.printer.generate_sketchmap import (
    generate,
    get_result_path,
    get_status_link,
)
from sketch_map_tool.printer.modules.generate_pdf import generate_pdf
from sketch_map_tool.printer.modules.paper_formats.paper_formats import (
    A0,
    A1,
    A2,
    A3,
    A4,
    A5,
    LEDGER,
    LEGAL,
    LETTER,
    TABLOID,
    PaperFormat,
)

OUTPUT_PATH = "./test_output/"
if not os.path.exists(OUTPUT_PATH):
    os.mkdir(OUTPUT_PATH)

DUMMY_BBOX = Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373")

generate_pdf.RESOURCE_PATH = "../../sketch_map_tool/printer/modules/resources/"


@pytest.mark.parametrize(
    "paper_format", [A0, A1, A2, A3, A4, A5, LEGAL, LETTER, LEDGER, TABLOID]
)
@pytest.mark.parametrize(
    "second_run", [False, True]
)  # When result files already exist for a given date,
#                                   the path should be returned directly
def test_generate(paper_format: PaperFormat, second_run: bool) -> None:
    """
    Test the function generate with different paper formats and starting a
    new sketch map generation as well as repeating a call already completed.
    """
    with patch("requests.get") as mock:

        mock.return_value = DummyResponse(
            open(  # pylint: disable=R1732
                "./test_data/dummy_map_img_landscape.jpg", "rb"
            )
        )
        result_path = generate(
            paper_format=paper_format,
            bbox=DUMMY_BBOX,
            resolution=(500, 600),
            output_path=OUTPUT_PATH,
        )
    if second_run:
        mock.assert_not_called()
    else:
        mock.assert_called_once_with(
            WMS_BASE_URL,
            {
                "REQUEST": "GetMap",
                "FORMAT": "image/png",
                "TRANSPARENT": "FALSE",
                "LAYERS": WMS_LAYERS,
                "WIDTH": 500,
                "HEIGHT": 600,
                "SRS": "EPSG:4326",
                "STYLES": "",
                "BBOX": "8.66100311,49.3957813,8.7166214,49.4265373",
            },
            stream=True,
            timeout=TIMEOUT_REQUESTS,
        )
    result_template_path = result_path.replace(".pdf", "_template.jpg")
    status_path = result_path.replace(".pdf", ".status")
    assert os.path.isfile(result_path)
    assert os.path.isfile(result_template_path)
    assert os.path.isfile(status_path)
    with open(status_path, encoding="utf8") as fr:
        assert (
            fr.read()
            == f"""Loading map image...
Generating Sketch Map PDF file...
Completed
{result_path.replace(OUTPUT_PATH, GENERATION_OUTPUT_LINK)}
"""
        )  # nosec
    if second_run:
        os.remove(result_path)
        os.remove(result_template_path)
        os.remove(status_path)


def test_get_result_path() -> None:
    """
    Test the function get_result_path.
    """
    assert (
        get_result_path(A2, DUMMY_BBOX, "test/bla", "21-12-24")
        == f"test/bla/21-12-24__{DUMMY_BBOX.get_str(mode='minus')}__a2.pdf"
    )


def test_get_status_link() -> None:
    """
    Test the function get_status_link.
    """
    assert (
        get_status_link(A2, DUMMY_BBOX, "21-12-24")
        == f"../status?mode=generation&format=a2&bbox={DUMMY_BBOX.get_str(mode='comma')}&d=21-12-24"
    )
