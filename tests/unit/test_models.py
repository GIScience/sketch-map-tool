from sketch_map_tool import models


def test_bbox(bbox_as_list):
    bbox = models.Bbox(*bbox_as_list)
    assert bbox.lat_min == 964598.2387041415
    assert bbox.lon_min == 6343922.275917276
    assert bbox.lat_max == 967350.9272435782
    assert bbox.lon_max == 6346262.602545459


def test_size(size_as_dict):
    size = models.Size(**size_as_dict)
    assert size.width == 1867
    assert size.height == 1587


def test_literatur_reference():
    literature_referece = models.LiteratureReference(
        img_src="ijgi-10-00130-g002.webp",
        citation="Klonner, C., Hartmann, M., Dischl, R., Djami, L., Anderson, L., Raifer, M., Lima-Silva, F., Degrossi, L. C., Zipf, A., de Albuquerque, J. P. (2021): The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data for Participatory Mapping, 10(3): 130. ISPRS International Journal of Geo-Information. 10:130.",
        url="https://doi.org/10.3390/ijgi10030130",
    )
    assert (
        literature_referece.img_src
        == "assets/images/about/publications/ijgi-10-00130-g002.webp"
    )
    assert (
        literature_referece.citation
        == "Klonner, C., Hartmann, M., Dischl, R., Djami, L., Anderson, L., Raifer, M., Lima-Silva, F., Degrossi, L. C., Zipf, A., de Albuquerque, J. P. (2021): The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data for Participatory Mapping, 10(3): 130. ISPRS International Journal of Geo-Information. 10:130."
    )
    assert literature_referece.url == "https://doi.org/10.3390/ijgi10030130"
