"""Tests for the module printer/modules/generate_pdf.py"""
import filecmp
import os
from pathlib import Path

import fitz
import pytest
from PIL import Image

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


@pytest.fixture
def expected_sketch_map(request) -> tuple:
    """Return paths of complete Sketch Map and the Sketch Map template (Map Area)."""
    orientation = request.getfixturevalue("orientation")
    paper_format = request.getfixturevalue("paper_format")
    directory = Path(__file__).parent / "fixtures" / "expected" / orientation
    return (
        directory / f"{paper_format}.jpg",
        directory / f"{paper_format}_template.jpg",
    )


@pytest.fixture
def map_image(request):
    """Map image from WMS."""
    orientation = request.getfixturevalue("orientation")
    p = Path(__file__).parent / "fixtures/dummy_map_img_{0}.jpg".format(orientation)
    return Image.open(p)


@pytest.mark.parametrize(
    "paper_format", [A0, A1, A2, A3, A4, A5, LEGAL, LETTER, LEDGER, TABLOID]
)
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_generate_pdf(
    bbox,
    expected_sketch_map,
    map_image,
    paper_format: PaperFormat,
    orientation: str,
    tmp_path: Path,
) -> None:
    """
    Test the function generate_pdf with a map image causing the sketch map
    to be in landscape or portrait orientation.
    """
    output_path = str(tmp_path / "sketch_map.pdf")
    result_path = generate_pdf.generate_pdf(
        output_path,
        map_image,
        bbox,
        "2021-12-24",
        paper_format,
    )
    result_template_path = result_path.replace(".pdf", "_template.jpg")
    fitz_pdf = fitz.open(result_path)
    pdf_img_path = result_path.replace(".pdf", ".jpg")
    fitz_pdf[0].get_pixmap().save(pdf_img_path)
    fitz_pdf.close()
    assert filecmp.cmp(
        pdf_img_path,
        expected_sketch_map[0],
        shallow=False,
    )
    assert filecmp.cmp(
        result_template_path,
        expected_sketch_map[1],
        shallow=False,
    )
    os.remove(result_path)
    os.remove(pdf_img_path)
    os.remove(result_template_path)
