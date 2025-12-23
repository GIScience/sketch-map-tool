from pathlib import Path

import pytest
from approvaltests import Options, verify_binary

from tests.comparator import GeoJSONComparator
from tests.namer import PytestNamer
from tests.reporter import SketchMapToolReporter


@pytest.fixture(scope="session")
def vector_path(tmp_path_factory, uuid_digitize) -> Path:
    return tmp_path_factory.getbasetemp() / uuid_digitize / "vector.geojson"


def test_smt_approver(sketch_map_marked_path, vector_path):
    options = (
        Options()
        .with_reporter(SketchMapToolReporter(sketch_map=sketch_map_marked_path))
        .with_comparator(GeoJSONComparator())
        .with_namer(PytestNamer())
    )
    with open(vector_path, "rb") as f:
        # TODO: One false positives for OAM based sketch map
        verify_binary(f.read(), ".geojson", options=options)
