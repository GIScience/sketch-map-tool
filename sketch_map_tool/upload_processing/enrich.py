from geojson import FeatureCollection


def enrich(fc: FeatureCollection, properties):
    """Enrich GeoJSON properties."""
    for feature in fc.features:
        feature.properties = feature.properties | properties
    return fc
