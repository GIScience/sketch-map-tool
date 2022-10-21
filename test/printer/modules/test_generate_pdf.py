"""
Tests for the module printer/modules/generate_pdf.py
"""
import filecmp
import os

import fitz
import pytest
from PIL import Image

from sketch_map_tool.helper_modules.bbox_utils import Bbox
from sketch_map_tool.printer.modules import generate_pdf
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

OUTPUT_PATH = "./test_output/sketch_map.pdf"
DUMMY_BBOX = Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373")

generate_pdf.RESOURCE_PATH = "../../../sketch_map_tool/printer/modules/resources/"


@pytest.fixture
def outfile(request):
    paper_format = request.getfixturevalue("paper_format")
    orientation = request.getfixturevalue("orientation")
    return "test_data/expected/{0}/{1}.jpg".format(paper_format, orientation)


@pytest.fixture
def infile(request):
    orientation = request.getfixturevalue("orientation")
    return Image.open(f"test_data/dummy_map_img_{orientation}.jpg")


@pytest.mark.parametrize(
    "paper_format", [A0, A1, A2, A3, A4, A5, LEGAL, LETTER, LEDGER, TABLOID]
)
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_generate_pdf(
    infile, outfile, paper_format: PaperFormat, orientation: str
) -> None:
    """
    Test the function generate_pdf with a map image causing the sketch map
    to be in landscape or portrait orientation.
    """
    result_path = generate_pdf.generate_pdf(
        OUTPUT_PATH, infile, DUMMY_BBOX, "2021-12-24", paper_format
    )
    result_template_path = result_path.replace(".pdf", "_template.jpg")
    fitz_pdf = fitz.open(result_path)
    pdf_img_path = result_path.replace(".pdf", ".jpg")
    fitz_pdf[0].get_pixmap().save(pdf_img_path)
    fitz_pdf.close()
    assert filecmp.cmp(
        pdf_img_path,
        outfile,
        shallow=False,
    )
    assert filecmp.cmp(
        result_template_path,
        outfile,
        shallow=False,
    )
    os.remove(result_path)
    os.remove(pdf_img_path)
    os.remove(result_template_path)
