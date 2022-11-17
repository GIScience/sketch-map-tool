import pytest
from sketch_map_tool.models import PaperFormat

# TODO re-add LEGAL
from sketch_map_tool.definitions import A0, A1, A2, A3, A4, LETTER, TABLOID


# TODO re-add LEGAL
@pytest.mark.parametrize(
    "format_",
    (
        A0,
        A1,
        A2,
        A3,
        A4,
        LETTER,
        TABLOID,
    ),
)
def test_paper_format(format_):
    assert isinstance(format_, PaperFormat)
