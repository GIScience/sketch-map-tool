import geojson
from geojson import FeatureCollection

from sketch_map_tool.definitions import COLORS


def post_process(fc: FeatureCollection, name: str) -> FeatureCollection:
    fc = clean(fc)
    fc = enrich(fc, properties={"name": name})
    return fc


def clean(fc: FeatureCollection) -> FeatureCollection:
    """Clean GeoJSON.

    Delete all polygons, which do not have the value 255 (are no markings).
    Delete all inner rings inside the polygons.
    """
    # f   -> feature
    # fc  -> feature collection
    fc.features = [f for f in fc.features if f.properties["color"] != "0"]
    for f in fc.features:
        if not isinstance(f.geometry, geojson.Polygon):
            raise TypeError(
                "geojson should never contain another geometry type than Polygon"
            )
        f.geometry.coordinates = [f.geometry.coordinates[0]]  # Delete inner ring
    return fc


def enrich(fc: FeatureCollection, properties):
    """Enrich GeoJSON properties and map colors."""
    for feature in fc.features:
        feature.properties = feature.properties | properties
        if "color" in feature.properties.keys():
            feature.properties["color"] = COLORS[feature.properties["color"]]
    return fc
