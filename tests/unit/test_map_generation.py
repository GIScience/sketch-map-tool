import os
from io import BytesIO

import numpy as np
import pymupdf
import pytest
from PIL import Image
from pytest_approval.main import verify_image
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas

from sketch_map_tool.definitions import A0, A1, A2, A3, A4, LETTER, TABLOID
from sketch_map_tool.map_generation import create_qr_code as generate_qr_code
from sketch_map_tool.map_generation.generate_pdf import (
    generate_pdf,
    get_aruco_markers,
    get_compass,
    pdf_page_to_img,
)
from sketch_map_tool.models import PaperFormat
from tests import FIXTURE_DIR
from tests import vcr_app as vcr


@pytest.fixture
def pdf():
    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    canv.drawString(100, 100, "Quality Report")
    canv.save()
    buffer.seek(0)
    return buffer


@pytest.fixture
def map_image(request):
    """Map image from WMS."""
    orientation = request.getfixturevalue("orientation")
    p = FIXTURE_DIR / "map-img-{}.jpg".format(orientation)
    return Image.open(p)


@pytest.fixture
def qr_code(uuid, bbox, format_, layer):
    return generate_qr_code(uuid, bbox, layer, format_)


@pytest.fixture
def qr_code_approval(uuid, bbox, monkeypatch):
    """QR code with fewer parameters for approval tests."""
    monkeypatch.setattr(
        "sketch_map_tool.map_generation.qr_code.__version__",
        "2026.7.2",
    )
    return generate_qr_code(uuid, bbox, "osm", A4)


@pytest.mark.parametrize("paper_format", [A0, A1, A2, A3, A4, LETTER, TABLOID])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
@vcr.use_cassette
def test_generate_pdf(
    map_image,
    qr_code,
    paper_format: PaperFormat,
    orientation,
    layer,
) -> None:
    sketch_map, sketch_map_template = generate_pdf(
        map_image,
        qr_code,
        paper_format,
        1283.129,
        layer,
    )
    assert isinstance(sketch_map, BytesIO)
    assert isinstance(sketch_map_template, BytesIO)


# NOTE: To reduce number of approvals, parameter numbers are kept low.
@pytest.mark.parametrize("orientation", ["landscape"])
@pytest.mark.parametrize("paper_format", [A4])
@pytest.mark.skipif(os.getenv("CI") is not None, reason="Detected CI environment")
def test_generate_pdf_sketch_map_approval(
    map_image,
    qr_code_approval,
    paper_format,
    orientation,
    monkeypatch,
) -> None:
    sketch_map, _ = generate_pdf(
        map_image,
        qr_code_approval,
        paper_format,
        1283.129,
        "osm",
    )
    # NOTE: The resulting PDFs across multiple test runs have slight non-visual
    # differences leading to a failure when using `verify_binary` on the PDFs.
    # That is why here they are converted to images for comparison first.
    with pymupdf.open(stream=sketch_map, filetype="pdf") as doc:
        # NOTE: For high resolution needed to read images such as aruco markers
        # matrix would have to be defined and given to get_pixmap.
        # This would result in larger file sizes.
        image = doc.load_page(0).get_pixmap().tobytes(output="png")
    assert verify_image(image, extension=".png")


# NOTE: To reduce number of approvals, parameter numbers are kept low.
@pytest.mark.parametrize("paper_format", [A4])
@pytest.mark.parametrize("orientation", ["landscape"])
@pytest.mark.skipif(os.getenv("CI") == "true", reason="detected CI environment")
def test_generate_pdf_sketch_map_template_approval(
    map_image,
    qr_code_approval,
    paper_format: PaperFormat,
    orientation,  # type: ignore
) -> None:
    _, sketch_map_template = generate_pdf(
        map_image,
        qr_code_approval,
        paper_format,
        1283.129,
        "osm",
    )
    assert verify_image(
        sketch_map_template.read(),
        extension=".png",
    )


def test_get_compass(format_):
    compass = get_compass(format_.compass_scale)
    assert isinstance(compass, Drawing)


def test_pdf_page_to_img(pdf):
    img_buffer = pdf_page_to_img(pdf, img_format="png")
    try:
        img = Image.open(img_buffer)  # noqa
        # img.show()  # For manual visual test
        assert True
    except:  # noqa
        assert False


def test_get_aruco_makers():
    markers = get_aruco_markers(size=100)
    assert len(markers) == 8
    for m in markers:
        assert isinstance(m, np.ndarray)
        buffer = BytesIO()
        Image.fromarray(m).save(buffer, format="PNG")
        assert verify_image(buffer.getvalue(), extension=".png", content_only=True)
