import os

import toml
from sketch_map_tool import __version__ as version


def test_version():
    infile = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "pyproject.toml"
    )
    with open(infile, "r") as fo:
        project_file = toml.load(fo)
        pyproject_version = project_file["tool"]["poetry"]["version"]
    assert pyproject_version == version
