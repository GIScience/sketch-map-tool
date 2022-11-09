import pytest

from sketch_map_tool.map_generation.paper_format import (
    A0,
    A1,
    A2,
    A3,
    A4,
    A5,
    LEGAL,
    LETTER,
    TABLOID,
    PaperFormat,
)


@pytest.mark.parametrize(
    "format_",
    (
        A0,
        A1,
        A2,
        A3,
        A4,
        A5,
        LEGAL,
        LETTER,
        TABLOID,
    ),
)
def test_paper_format(format_):
    assert isinstance(format_, PaperFormat)
