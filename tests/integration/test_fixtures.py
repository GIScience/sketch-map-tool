"""Test if fixtures are created successfully"""


def test_sketch_map_pdf(sketch_map_pdf):
    assert sketch_map_pdf is not None
    assert len(sketch_map_pdf) > 0


def test_sketch_map_png(sketch_map_png):
    assert sketch_map_png is not None
    assert len(sketch_map_png) > 0


def test_vector(vector):
    assert vector is not None
    assert len(vector) > 0


def test_raster(raster):
    assert raster is not None
    assert len(raster) > 0


def test_map_frame_marked(map_frame_marked):
    assert map_frame_marked is not None
    assert map_frame_marked.size is not None
