import geojson
from geojson import FeatureCollection
from shapely.geometry import shape
from shapely import Polygon, MultiPolygon
from shapely.geometry import mapping
from shapely.ops import cascaded_union
from shapelysmooth import chaikin_smooth

from sketch_map_tool.definitions import COLORS

from typing import Union

def post_process(fc: FeatureCollection, name: str) -> FeatureCollection:
    fc = clean(fc)
    fc = enrich(fc, properties={"name": name})
    fc = simplify(fc)
    fc = smooth(fc)
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


def simplify(fc: FeatureCollection) -> FeatureCollection:
    """
    Simplifies the geometries in a GeoJSON FeatureCollection.

    This function simplifies the geometries in a given FeatureCollection. It applies a buffer operation
    to each geometry based on a percentage of the maximum width, dissolves the geometries based on a
    'color' attribute, removes inner rings, and then re-applies a negative buffer to restore the original
    size. The function assumes that the 'color' field exists in the properties of the features.

    Parameters:
    - fc (geojson.FeatureCollection): The FeatureCollection to be simplified.

    Returns:
    - geojson.FeatureCollection: The simplified FeatureCollection.
    """
    features = fc["features"]
    properties = features[0]["properties"]

    geometries = [shape(feature["geometry"]) for feature in features]

    # Buffer operation
    buffer_distance_percentage = 0.1
    max_diag = max(
        ((geometry.bounds[2] - geometry.bounds[0]) ** 2 + (geometry.bounds[3] - geometry.bounds[1]) ** 2) ** 0.5 for
        geometry in geometries)  # check for webmercator
    buffer_distance = buffer_distance_percentage * max_diag
    buffered_geometries = [geometry.buffer(buffer_distance) for geometry in geometries]
    # Dissolve by color field (assuming there's a "color" field)
    try:
        dissolved_geometrie = [remove_inner_rings(geometry) for geometry in cascaded_union(buffered_geometries)]
    except:
        dissolved_geometrie = [remove_inner_rings(geometry) for geometry in [cascaded_union(buffered_geometries)]]

    simplified_geometries = [geometry.buffer(-buffer_distance).simplify(0.0025 * max_diag) for geometry in dissolved_geometrie]

    # Create a single GeoJSON feature
    features = [geojson.Feature(
        geometry=mapping(geometry),
        properties=properties
    ) for geometry in simplified_geometries]

    # Create a GeoJSON feature collection with the single feature
    fc = geojson.FeatureCollection(features)
    return fc


def remove_inner_rings(geometry: Polygon | MultiPolygon) -> Polygon  | MultiPolygon:
    """
    Removes inner rings (holes) from a given Shapely geometry object.

    This function checks the type of the geometry object. If it is a Polygon, it creates
    a new Polygon with just the exterior ring. If it is a MultiPolygon, it does the same
    for each Polygon in it. Other geometry types are not supported and will raise an error.

    Parameters:
    - geometry (Polygon, MultiPolygon): A Shapely geometry object, either a Polygon or MultiPolygon.

    Returns:
    - Polygon, MultiPolygon: A Shapely geometry object with inner rings removed.
    """
    if geometry.is_empty:
        return geometry
    elif geometry.type == 'Polygon':
        return Polygon(geometry.exterior)
    elif geometry.type == 'MultiPolygon':
        return MultiPolygon([Polygon(poly.exterior) for poly in geometry.geoms])
    else:
        raise ValueError("Unsupported geometry type")


def smooth(fc: FeatureCollection) -> FeatureCollection:
    """
    Smoothens the polygon geometries in a GeoJSON FeatureCollection.

    This function applies a Chaikin smoothing algorithm to each polygon geometry in the given
    FeatureCollection. Non-polygon geometries are skipped. The function updates the geometries
    while retaining the properties of each feature.

    Parameters:
    - fc (geojson.FeatureCollection): The FeatureCollection to be smoothed.

    Returns:
    - geojson.FeatureCollection: The FeatureCollection with smoothed polygon geometries.
    """
    features = fc["features"]
    updated_features = []

    for feature in features:
        geometry = feature["geometry"]
        properties = feature["properties"]

        if geometry["type"] == "Polygon":
            geometry = Polygon(geometry["coordinates"][0])
        else:
            continue  # Skip non-polygon geometries

        corrected_geometry = chaikin_smooth(geometry)

        updated_features.append(geojson.Feature(
            geometry=mapping(corrected_geometry),
            properties=properties
        ))

    # Create a GeoJSON feature collection with the updated features
    fc = geojson.FeatureCollection(updated_features)
    return fc

