from geojson import FeatureCollection, Feature
from shapely.geometry import shape, Polygon, mapping, MultiPolygon
from shapely.ops import cascaded_union

def remove_inner_rings(geometry):
    """
    Remove inner rings (holes) from a Shapely geometry.

    Parameters:
    - geometry (shapely.geometry.base.BaseGeometry): Input geometry.

    Returns:
    - shapely.geometry.base.BaseGeometry: Output geometry without inner rings.
    """
    if geometry.is_empty:
        return geometry
    elif geometry.type == 'Polygon':
        return Polygon(geometry.exterior)
    elif geometry.type == 'MultiPolygon':
        return MultiPolygon([Polygon(poly.exterior) for poly in geometry.geoms])
    else:
        raise ValueError("Unsupported geometry type")


def postprocess(feature_collection: FeatureCollection):
    """
    Postprocess a GeoJSON FeatureCollection by buffering, dissolving, removing inner rings, and simplifying.

    Parameters:
    - feature_collection (dict): GeoJSON FeatureCollection.

    Returns:
    - geojson.FeatureCollection: Modified GeoJSON FeatureCollection.
    """
    # Extract properties from the first feature
    properties = feature_collection["features"][0]["properties"]

    # Convert FeatureCollection to Shapely geometries
    geometries = [shape(feature["geometry"]) for feature in feature_collection["features"]]

    # Buffer operation
    buffer_distance_percentage = 0.1
    max_width = max(geometry.bounds[2] - geometry.bounds[0] for geometry in geometries)
    buffer_distance = buffer_distance_percentage * max_width
    buffered_geometries = [geometry.buffer(buffer_distance) for geometry in geometries]

    # Dissolve by color field (assuming there's a "color" field)
    try:
        dissolved_geometries = [remove_inner_rings(geometry) for geometry in cascaded_union(buffered_geometries)]
    except:
        dissolved_geometries = [remove_inner_rings(geometry) for geometry in [cascaded_union(buffered_geometries)]]

    # Buffer back (negative distance)
    buffered_geometries = [geometry.buffer(-buffer_distance) for geometry in dissolved_geometries]

    # Simplify geometries
    simplified_geometries = [geometry.simplify(0.2 * buffer_distance) for geometry in buffered_geometries]

    # Create GeoJSON features
    features = [Feature(geometry=mapping(geometry), properties=properties) for geometry in simplified_geometries]

    # Create GeoJSON feature collection
    feature_collection = FeatureCollection(features)
    return feature_collection
