from io import BytesIO

import pytest
from PIL import Image
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from sketch_map_tool.map_generation.generate_pdf import (
    get_compass,
    get_globes,
    pdf_page_to_img,
)


@pytest.fixture
def pdf():
    buffer = BytesIO()
    canv = canvas.Canvas(buffer, pagesize=A4)
    canv.drawString(100, 100, "Quality Report")
    canv.save()
    buffer.seek(0)
    return buffer


def test_get_globes(format_):
    globes = get_globes(format_.globe_scale)
    for globe in globes:
        assert isinstance(globe, Drawing)


def test_get_compass(format_):
    compass = get_compass(format_.compass_scale)
    assert isinstance(compass, Drawing)


def test_pdf_page_to_img(pdf):
    img_buffer = pdf_page_to_img(pdf)
    try:
        img = Image.open(img_buffer)  # noqa
        # img.show()  # For manual visual test
        assert True
    except:  # noqa
        assert False
