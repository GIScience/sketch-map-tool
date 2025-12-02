import pytest
from approvaltests import Options, verify_binary

from tests.comparator import GeoJSONComparator
from tests.namer import PytestNamer
from tests.reporter import SketchMapToolReporter


@pytest.fixture(scope="session")
def vector_path(tmp_path_factory, uuid_digitize) -> bytes:
    return tmp_path_factory.getbasetemp() / uuid_digitize / "vector.geojson"


@pytest.mark.usefixtures("sketch_map_marked")
@pytest.fixture(scope="session")
def sketch_map_marked_path(tmp_path_factory, uuid_create) -> bytes:
    return tmp_path_factory.getbasetemp() / uuid_create / "sketch-map-marked.png"


def test_smt_approver(sketch_map_marked_path, vector_path, layer):
    options = (
        Options()
        .with_reporter(SketchMapToolReporter(sketch_map=sketch_map_marked_path))
        .with_comparator(GeoJSONComparator())
        .with_namer(PytestNamer())
    )
    with open(vector_path, "rb") as f:
        verify_binary(f.read(), ".geojson", options=options)
