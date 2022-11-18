from sketch_map_tool import models


def test_bbox(bbox_as_list):
    bbox = models.Bbox(*bbox_as_list)
    assert bbox.lon_min == 964598.2387041415
    assert bbox.lat_min == 6343922.275917276
    assert bbox.lon_max == 967350.9272435782
    assert bbox.lat_max == 6346262.602545459


def test_size(size_as_dict):
    size = models.Size(**size_as_dict)
    assert size.width == 1867
    assert size.height == 1587
