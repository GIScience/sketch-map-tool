from io import BytesIO

import geojson


def clean(fc_buffer):
    """Clean GeoJSON.

    Delete all polygons, which do not have the value 255 (are no markings).
    Delete all inner rings inside the polygons.
    """
    # f   -> feature
    # fc  -> feature collection
    fc = geojson.load(fc_buffer)
    fc.features = [f for f in fc.features if f.properties["color"] == "255"]
    for f in fc.features:
        assert isinstance(f.geometry, geojson.Polygon)
        f.geometry.coordinates = [f.geometry.coordinates[0]]  # Delete inner ring
    return BytesIO(geojson.dumps(fc).encode("utf-8"))
