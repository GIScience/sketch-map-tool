from sketch_map_tool import definitions


def test_get_literatur_references():
    result = definitions.get_literature_references()
    assert (
        result[0].img_src
        == "/static/assets/images/about/publications/ijgi-10-00130-g002.webp"
    )
    assert result[0].citation == (
        "Klonner, C., Hartmann, M., Dischl, R., Djami, L., Anderson, L.,"
        " Raifer, M., Lima-Silva, F., Degrossi, L. C., Zipf, A., de Albuquerque,"
        " J. P. (2021): The Sketch Map Tool Facilitates the Assessment of "
        "OpenStreetMap Data for Participatory Mapping, 10(3): 130."
        " ISPRS International Journal of Geo-Information. 10:130."
    )
    assert result[0].url == "https://doi.org/10.3390/ijgi10030130"
