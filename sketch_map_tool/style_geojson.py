from geojson import FeatureCollection

from sketch_map_tool.definitions import COLOR_HEX, COLORS


def style(fc: FeatureCollection, num_of_uploads: int):
    """Style GeoJSON using simple-stylespec."""
    for feature in fc.features:
        if "color" in feature.properties.keys():
            continue

        color_name = COLORS[feature.properties["color"]]
        color_hex = COLOR_HEX[color_name]

        if feature["geometry"]["type"] == "Point":
            feature.properties["marker-color"] = color_hex
        else:
            feature.properties["color"] = color_name
            feature.properties["stroke"] = color_hex
            feature.properties["fill"] = color_hex
            feature.properties["fill-opacity"] = min(max(1 / num_of_uploads, 0.1), 0.8)
    return fc
