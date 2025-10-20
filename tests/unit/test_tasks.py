"""Test tasks without using the tasks queue Celery."""

from io import BytesIO

import fitz
from approvaltests import Options, verify_binary

from sketch_map_tool import tasks
from tests import vcr_app as vcr
from tests.comparator import ImageComparator
from tests.namer import PytestNamer
from tests.reporter import ImageReporter


@vcr.use_cassette
def test_generate_sketch_map(
    monkeypatch,
    bbox,
    bbox_wgs84,
    format_,
    size,
    scale,
    layer,
):
    monkeypatch.setattr(
        "sketch_map_tool.tasks.db_client_celery.insert_map_frame",
        lambda *_: None,
    )
    map_pdf = tasks.generate_sketch_map(
        bbox,
        bbox_wgs84,
        format_,
        "landscape",
        size,
        scale,
        layer,
    )

    assert isinstance(map_pdf, BytesIO)

    # NOTE: The resulting PDFs across multiple test runs have slight non-visual
    # differences leading to a failure when using `verify_binary` on the PDFs.
    # That is why here they are converted to images for comparison first.
    with fitz.open(stream=map_pdf, filetype="pdf") as doc:
        # NOTE: For high resolution needed to read images such as aruco markers
        # matrix would have to be defined and given to get_pixmap.
        # This would result in larger file sizes.
        image = doc.load_page(0).get_pixmap()  # type: ignore
    # fmt: off
    options = (
        Options()
            .with_reporter(ImageReporter())
            .with_namer(PytestNamer())
            .with_comparator(ImageComparator())
    )
    # fmt: off
    verify_binary(
        image.tobytes(output="png"),
        ".png",
        options=options,
    )
