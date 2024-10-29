from io import BytesIO
from pathlib import Path

import fitz
import numpy as np
import pytest
from approvaltests import Options, verify_binary
from PIL import Image
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas

# TODO re-add LEGAL
from sketch_map_tool.definitions import A0, A1, A2, A3, A4, LETTER, TABLOID
from sketch_map_tool.map_generation import qr_code as generate_qr_code
from sketch_map_tool.map_generation.generate_pdf import (
    generate_pdf,
    get_aruco_markers,
    get_compass,
    get_globes,
    pdf_page_to_img,
)
from sketch_map_tool.models import PaperFormat
from tests import FIXTURE_DIR
from tests.namer import PytestNamer, PytestNamerFactory
from tests.reporter import ImageReporter, NDArrayReporter
from tests.unit.helper import serialize_ndarray


@pytest.fixture
def pdf():
    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    canv.drawString(100, 100, "Quality Report")
    canv.save()
    buffer.seek(0)
    return buffer


# TODO: yield appropriate map image for ESRI layer
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
def qr_code(uuid, bbox, layer, format_):
    return generate_qr_code(uuid, bbox, layer, format_, "mock_version_number")


# TODO: re-add LEGAL
@pytest.mark.parametrize("paper_format", [A0, A1, A2, A3, A4, LETTER, TABLOID])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
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
    # NOTE: The resulting PDFs across multiple test runs have slight non-visual
    # differences leading to a failure when using `verify_binary` on the PDFs.
    # That is why here they are converted to images for comparison first.
    with fitz.open(stream=sketch_map, filetype="pdf") as doc:
        # NOTE: For high resolution needed to read images such as aruco markers
        # matrix has to be defined and given to get_pixmap. This will result in
        # larger file sizes.
        image = doc.load_page(0).get_pixmap()  # type: ignore
    # fmt: off
    options = (
        Options()
            .with_reporter(ImageReporter())
            .with_namer(PytestNamer())
    )
    # fmt: off
    verify_binary(
        image.tobytes(output="png"),
        ".png",
        options=options,
    )


@pytest.mark.parametrize("paper_format", [A0, A1, A2, A3, A4, LETTER, TABLOID])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
def test_generate_sketch_map_template(
    map_image,
    qr_code,
    paper_format: PaperFormat,
    orientation,  # pyright: ignore reportUnusedVariable
    layer,
) -> None:
    _, sketch_map_template = generate_pdf(
        map_image,
        qr_code,
        paper_format,
        1283.129,
        layer,
    )
    assert isinstance(sketch_map_template, BytesIO)
    # fmt: off
    options = (
        Options()
            .with_reporter(ImageReporter())
            .with_namer(PytestNamer())
    )
    # fmt: on
    verify_binary(
        sketch_map_template.read(),
        ".png",
        options=options,
    )


def test_get_globes(format_):
    globes = get_globes(format_.globe_scale)
    for globe in globes:
        assert isinstance(globe, Drawing)


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
    markers = get_aruco_markers()
    assert len(markers) == 4
    for i, m in enumerate(markers):
        assert isinstance(m, np.ndarray)
        options = (
            Options()
            .with_reporter(NDArrayReporter())
            .with_namer(PytestNamerFactory.with_parameters(i))
        )
        # fmt: on
        verify_binary(
            serialize_ndarray(m),
            ".npy",
            options=options,
        )
        # NOTE: Uncomment to display markers
        # import cv2
        # cv2.imshow("Marker", m)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # fmt: off
