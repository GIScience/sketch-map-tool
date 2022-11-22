from sketch_map_tool import models


def test_bbox(bbox_as_list):
    bbox = models.Bbox(*bbox_as_list)
    assert bbox.lon_min == 964472.1973848869
    assert bbox.lat_min == 6343459.035638228
    assert bbox.lon_max == 967434.6098457306
    assert bbox.lat_max == 6345977.635778541


def test_size(size_as_dict):
    size = models.Size(**size_as_dict)
    assert size.width == 1867
    assert size.height == 1587
