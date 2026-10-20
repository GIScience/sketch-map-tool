from geojson import FeatureCollection

from sketch_map_tool.definitions import COLORS


def style(fc: FeatureCollection, num_of_uploads: int):
    """Style GeoJSON using simple-stylespec."""
    for feature in fc.features:
        if "color" in feature.properties.keys():
            color = COLORS[feature.properties["color"]]
            feature.properties["color"] = color
            feature.properties["stroke"] = color
            feature.properties["fill"] = color
            feature.properties["fill-opacity"] = max(1 / num_of_uploads, 0.1)
    return fc
