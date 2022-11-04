import pytest

from sketch_map_tool.map_generation.paper_format import PaperFormat, paper_format


@pytest.mark.parametrize(
    "format_",
    ["a0", "a1", "a2", "a3", "a4", "a5", "legal", "tabloid", "ledger", "letter"],
)
def test_paper_format(format_):
    pf = paper_format(format_)
    assert isinstance(pf, PaperFormat)
