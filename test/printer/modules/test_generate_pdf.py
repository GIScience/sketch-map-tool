"""
Tests for the module printer/modules/generate_pdf.py
"""
import os
import pytest
from PIL import Image
from helper_modules.bbox_utils import Bbox
from printer.modules import generate_pdf
from printer.modules.paper_formats.paper_formats import (A0, A1, A2, A3, A4, A5, LEGAL, LETTER,
                                                         LEDGER, TABLOID, PaperFormat)

OUTPUT_DIR = "./test_output/"  # Will be temporarily created and removed after the tests
DUMMY_BBOX = Bbox.bbox_from_str("8.66100311,49.3957813,8.71662140,49.4265373")

generate_pdf.RESOURCE_PATH = "../../../printer/modules/resources/"


@pytest.mark.parametrize("paper_format", [A0, A1, A2, A3, A4, A5, LEGAL, LETTER, LEDGER, TABLOID])
def test_generate_pdf_landscape(paper_format: PaperFormat) -> None:
    """
    Test for the function generate_pdf with a map image causing the sketch map to be in landscape
    orientation.
    """
    os.mkdir(OUTPUT_DIR)
    map_image = Image.open("../test_data/dummy_map_img_landscape.jpg")
    result_path = generate_pdf.generate_pdf(OUTPUT_DIR,
                                            map_image,
                                            DUMMY_BBOX,
                                            "2021-12-24",
                                            paper_format)
    os.remove(OUTPUT_DIR)
    # TODO: Compare resulting PDF with expected one under test_data/expected/generate_pdf/


def test_generate_pdf_portrait() -> None:
    """
    Test for the function generate_pdf with a map image causing the sketch map to be in portrait
    orientation.
    """
    pass  # TODO
