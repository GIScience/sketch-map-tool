from pathlib import Path

from sketch_map_tool.helper_modules import helper


def test_get_project_root():
    expected = Path(__file__).resolve().parent.parent.parent.resolve()
    result = helper.get_project_root()
    assert expected == result
