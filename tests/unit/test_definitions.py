from sketch_map_tool import definitions
from sketch_map_tool.models import Layer


def test_get_literatur_references():
    result = definitions.get_literature_references()
    for r in result:
        assert r.img_src is not None
        assert r.citation is not None


def test_get_attribution(layer):
    # It is possible that the attribution text retrieved from the ESRI API changes
    result = definitions.get_attribution(layer)
    if layer == "osm":
        assert result == "Powered by OpenStreetMap<br />©openstreetmap.org/copyright"
    if layer == "esri-world-imagery":
        assert result == (
            "Powered by Esri<br />Source: Esri, Maxar, GeoEye, Earthstar "
            + "Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS "
            + "User Community"
        )


def test_get_attribution_no_esri_esri_api_key(monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.definitions.get_config_value",
        lambda _: "",
    )
    result = definitions.get_attribution(Layer("esri-world-imagery"))
    assert result == (
        "Powered by Esri<br />Esri, Maxar, Earthstar Geographics, and the GIS User "
        + "Community"
    )
