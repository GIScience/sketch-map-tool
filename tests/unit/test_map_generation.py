from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas

# TODO re-add LEGAL
from sketch_map_tool.definitions import A0, A1, A2, A3, A4, LETTER, TABLOID
from sketch_map_tool.map_generation import qr_code as generate_qr_code
from sketch_map_tool.map_generation.generate_pdf import (
    generate_pdf,
    get_compass,
    get_globes,
    pdf_page_to_img,
)
from sketch_map_tool.models import PaperFormat
from tests import FIXTURE_DIR
from tests.unit.helper import save_test_file


@pytest.fixture
def pdf():
    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    canv.drawString(100, 100, "Quality Report")
    canv.save()
    buffer.seek(0)
    return buffer


@pytest.fixture
def expected_sketch_map(request) -> tuple:
    """Return paths of complete Sketch Map and the Sketch Map template (Map Area)."""
    paper_format = request.getfixturevalue("paper_format")
    directory = (
        Path(__file__).parent
        / "fixtures"
        / "expected"
        / request.getfixturevalue("orientation")
    )
    return (
        directory / "{}.jpg".format(paper_format.title),
        directory / "{}_template.jpg".format(paper_format.title),
    )


@pytest.fixture
def map_image(request):
    """Map image from WMS."""
    orientation = request.getfixturevalue("orientation")
    p = FIXTURE_DIR / "map-img-{}.jpg".format(orientation)
    return Image.open(p)


@pytest.fixture
def map_image_too_big(request):
    """Map image from WMS exceeding the limit on map frame size"""
    orientation = request.getfixturevalue("orientation")
    p = FIXTURE_DIR / "map-img-big-{}.jpg".format(orientation)
    return Image.open(p)


@pytest.fixture
def qr_code(bbox, format_, size):
    return generate_qr_code(
        str(uuid4()),
        bbox,
        format_,
    )


# TODO re-add LEGAL
@pytest.mark.parametrize("paper_format", [A0, A1, A2, A3, A4, LETTER, TABLOID])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_generate_pdf(
    map_image,
    qr_code,
    paper_format: PaperFormat,
    orientation,
    expected_sketch_map,
    request,
) -> None:
    sketch_map, sketch_map_template = generate_pdf(
        map_image,
        qr_code,
        paper_format,
        1283.129,
    )
    assert isinstance(sketch_map, BytesIO)
    assert isinstance(sketch_map_template, BytesIO)
    # if you want the maps to be saved for visual inspection, use the parameter --save-maps with pytest
    save_test_file(
        request,
        "--save-maps",
        "debug-map-{}-{}.pdf".format(paper_format.title, orientation),
        sketch_map,
    )
    save_test_file(
        request,
        "--save-maps",
        "debug-map-template-{}-{}.png".format(paper_format.title, orientation),
        sketch_map_template,
    )
    # TODO:
    # assert filecmp.cmp(
    #     sketch_map,
    #     expected_sketch_map[0],
    #     shallow=False,
    # )
    # assert filecmp.cmp(
    #     sketch_map_template,
    #     expected_sketch_map[1],
    #     shallow=False,
    # )


@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_generate_pdf_map_frame_too_big(
    map_image_too_big,
    qr_code,
    orientation,
) -> None:
    sketch_map, sketch_map_template = generate_pdf(
        map_image_too_big,
        qr_code,
        A0,
        1283.129,
    )

    map_frame_img = Image.open(sketch_map_template)

    # Check that the upper limit on map frame size is enforced
    assert map_frame_img.width <= 2000 and map_frame_img.height <= 2000


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
