"""Test if fixtures are created successfully"""


def test_sketch_map(sketch_map):
    assert sketch_map is not None
    assert len(sketch_map) > 0


def test_map_frame(map_frame):
    assert map_frame is not None


def test_sketch_map_marked(sketch_map_marked):
    assert sketch_map_marked is not None
    assert len(sketch_map_marked) > 0


def test_map_frame_marked(map_frame_marked):
    assert map_frame_marked is not None
    assert map_frame_marked.size is not None


def test_vector(vector):
    assert vector is not None
    assert len(vector) > 0


def test_raster(raster):
    assert raster is not None
    assert len(raster) > 0
