import geojson
from geojson import FeatureCollection


def clean(fc: FeatureCollection) -> FeatureCollection:
    """Clean GeoJSON.

    Delete all polygons, which do not have the value 255 (are no markings).
    Delete all inner rings inside the polygons.
    """
    # f   -> feature
    # fc  -> feature collection
    fc.features = [f for f in fc.features if f.properties["color"] == "255"]
    for f in fc.features:
        if not isinstance(f.geometry, geojson.Polygon):
            raise TypeError(
                "geojson should never contain another geometry type than Polygon"
            )
        f.geometry.coordinates = [f.geometry.coordinates[0]]  # Delete inner ring
    return fc
