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


def test_get_attribution(layer):
    # It is possible that the attribution text retrieved from the ESRI API changes
    result = definitions.get_attribution(layer)
    assert result in (
        (
            "Powered by Esri<br />Source: Esri, Maxar, GeoEye, Earthstar Geographics, "
            + "CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community"
        ),
        ("Powered by OpenStreetMap<br />©openstreetmap.org/copyright"),
    )
