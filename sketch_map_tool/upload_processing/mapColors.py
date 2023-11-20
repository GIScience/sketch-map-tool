from geojson import FeatureCollection

def mapColors(fc: FeatureCollection, mapping):
    for feature in fc.features:
        feature.properties["color"] = mapping[feature.properties["color"]]
    return fc