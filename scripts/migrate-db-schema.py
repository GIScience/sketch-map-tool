# Create bbox_wgs84, centroid and centroid_wgs84 columns
# And put WKT inside.
# Transform bbox coordinates to WKT.
# Fix wrong lat / lon order


import psycopg2
import pyproj
import shapely
from shapely.geometry import Point, Polygon
from shapely.ops import transform


def transform_3857_to_4326(geom: Polygon | Point) -> Polygon | Point:
    wgs84 = pyproj.CRS("EPSG:4326")
    pseudo = pyproj.CRS("EPSG:3857")
    project = pyproj.Transformer.from_crs(pseudo, wgs84, always_xy=True).transform
    return transform(project, geom)


def bbox_to_centroid(bbox: Polygon) -> Point:
    return bbox.centroid


def select():
    query = "SELECT uuid, bbox, lon, lat FROM map_frame;"
    con = psycopg2.connect(host="localhost", port="5444", user="smt", password="smt")
    cur = con.cursor()
    cur.execute(query)
    result = cur.fetchall()
    con.commit()
    cur.close()
    con.close()

    migrated = []
    for row in result:
        uuid, bbox, lon, lat = row
        if bbox is not None or bbox != "":
            coords = bbox.split(",")
            bbox_ = shapely.geometry.box(
                coords[0],
                coords[1],
                coords[2],
                coords[3],
            )
            bbox_wgs84 = transform_3857_to_4326(bbox_)
            centroid = bbox_.centroid.wkt
            centroid_wgs84 = bbox_wgs84.centroid.wkt
            bbox_ = bbox_.wkt
            bbox_wgs84 = bbox_wgs84.wkt
        elif bbox is None or bbox == "":
            bbox_ = bbox
            bbox_wgs84 = bbox
            point = Point(lat, lon)  # NOTE: lat, lon where stored flipped in DB
            centroid = point.wkt
            centroid_wgs84 = transform_3857_to_4326(point).wkt
        else:
            continue
        migrated.append((bbox_, bbox_wgs84, centroid, centroid_wgs84, uuid))
    query = """
        UPDATE map_frame
        SET bbox = %s, bbox_wgs84 = %s, centroid = %s, centroid_wgs84= %s
        WHERE uuid = %s;
    """
    con = psycopg2.connect(host="localhost", port="5444", user="smt", password="smt")
    cur = con.cursor()
    cur.executemany(query, migrated)
    con.commit()
    cur.close()
    con.close()
    print("DONE")


if __name__ == "__main__":
    select()
