from io import BytesIO

import fitz
import numpy as np
import pytest
from approvaltests import Options, verify_binary
from PIL import Image
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas

from sketch_map_tool.definitions import A0, A1, A2, A3, A4, LETTER, TABLOID
from sketch_map_tool.map_generation import qr_code as generate_qr_code
from sketch_map_tool.map_generation.generate_pdf import (
    generate_pdf,
    get_aruco_markers,
    get_compass,
    pdf_page_to_img,
)
from sketch_map_tool.models import Layer, PaperFormat
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


@pytest.fixture
def map_image(request):
    """Map image from WMS."""
    orientation = request.getfixturevalue("orientation")
    p = FIXTURE_DIR / "map-img-{}.jpg".format(orientation)
    return Image.open(p)


@pytest.fixture
def qr_code(uuid, bbox, format_, layer):
    return generate_qr_code(uuid, bbox, layer, format_, "mock_version_number")


@pytest.fixture
def qr_code_approval(uuid, bbox):
    """QR code with fewer parameters for approval tests."""
    return generate_qr_code(uuid, bbox, Layer("osm"), A4, "mock_version_number")


@pytest.mark.parametrize("paper_format", [A0, A1, A2, A3, A4, LETTER, TABLOID])
@pytest.mark.parametrize("orientation", ["landscape", "portrait"])
@pytest.mark.parametrize("aruco_markers", [True, False])
def test_generate_pdf(
    map_image,
    qr_code,
    paper_format: PaperFormat,
    orientation,  # pyright: ignore reportUnusedVariable
    layer,
    aruco_markers,
) -> None:
    sketch_map, sketch_map_template = generate_pdf(
        map_image,
        qr_code,
        paper_format,
        1283.129,
        layer,
        aruco_markers,
    )
    assert isinstance(sketch_map, BytesIO)
    assert isinstance(sketch_map_template, BytesIO)


# NOTE: To reduce number of approvals, parameter numbers are kept low.
@pytest.mark.parametrize("orientation", ["landscape"])
@pytest.mark.parametrize("aruco_markers", [True, False])
def test_generate_pdf_sketch_map_approval(
    map_image,
    qr_code_approval,
    orientation,  # pyright: ignore reportUnusedVariable
    aruco_markers,
) -> None:
    sketch_map, _ = generate_pdf(
        map_image,
        qr_code_approval,
        A4,
        1283.129,
        Layer("osm"),
        aruco_markers,
    )
    # NOTE: The resulting PDFs across multiple test runs have slight non-visual
    # differences leading to a failure when using `verify_binary` on the PDFs.
    # That is why here they are converted to images for comparison first.
    with fitz.open(stream=sketch_map, filetype="pdf") as doc:
        # NOTE: For high resolution needed to read images such as aruco markers
        # matrix would have to be defined and given to get_pixmap.
        # This would result in larger file sizes.
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


# NOTE: To reduce number of approvals, parameter numbers are kept low.
@pytest.mark.parametrize("paper_format", [A4])
@pytest.mark.parametrize("orientation", ["landscape"])
@pytest.mark.parametrize("aruco_markers", [True, False])
def test_generate_pdf_sketch_map_template_approval(
    map_image,
    qr_code_approval,
    paper_format: PaperFormat,
    orientation,  # pyright: ignore reportUnusedVariable
    aruco_markers,
) -> None:
    _, sketch_map_template = generate_pdf(
        map_image,
        qr_code_approval,
        paper_format,
        1283.129,
        Layer("osm"),
        aruco_markers,
    )
    # fmt: off
    options = (
        Options()
            .with_reporter(ImageReporter())
            .with_namer(PytestNamer())
    )
    # fmt: off
    verify_binary(
        sketch_map_template.read(),
        ".png",
        options=options,
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
