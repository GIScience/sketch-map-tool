from pathlib import Path

from sketch_map_tool import helpers


def test_get_project_root():
    expected = Path(__file__).resolve().parent.parent.parent.resolve()
    result = helpers.get_project_root()
    assert expected == result
