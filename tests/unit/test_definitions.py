from sketch_map_tool import definitions


def test_get_literatur_references():
    result = definitions.get_literature_references()
    for r in result:
        assert r.img_src is not None
        assert r.citation is not None


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
