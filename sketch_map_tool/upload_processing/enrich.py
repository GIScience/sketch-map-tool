from geojson import FeatureCollection

from sketch_map_tool.definitions import COLORS


def enrich(fc: FeatureCollection, properties):
    """Enrich GeoJSON properties and map colors."""
    for feature in fc.features:
        feature.properties = feature.properties | properties
        if "color" in feature.properties.keys():
            feature.properties["color"] = COLORS[feature.properties["color"]]
    return fc
