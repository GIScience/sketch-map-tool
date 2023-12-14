from copy import deepcopy
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import geojson
from geojson import FeatureCollection
from osgeo import gdal, ogr
from pyproj import Transformer


def transform(feature: FeatureCollection) -> FeatureCollection:
    """Reproject GeoJSON from WebMercator to EPSG:4326"""
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    raw = geojson.utils.map_tuples(  # type: ignore
        lambda coordinates: transformer.transform(coordinates[0], coordinates[1]),
        deepcopy(feature),
    )
    return geojson.loads(geojson.dumps(raw))


def polygonize(geotiff: BytesIO, layer_name: str) -> FeatureCollection:
    """Produces a polygon feature layer (GeoJSON) from a raster (GeoTIFF)."""
    gdal.UseExceptions()
    ogr.UseExceptions()

    # open geotiff
    infile = NamedTemporaryFile(suffix=".geotiff")
    with open(infile.name, "wb") as f:
        f.write(geotiff.getbuffer())

    src_ds = gdal.Open(infile.name)
    srs = src_ds.GetSpatialRef()

    with TemporaryDirectory() as tmpdirname:
        outfile_name = Path(tmpdirname) / "out.geojson"

        # open geojson
        driver = ogr.GetDriverByName("GeoJSON")
        dst_ds = driver.CreateDataSource(str(outfile_name))

        dst_layer = dst_ds.CreateLayer(layer_name, srs=srs)
        dst_layer.CreateField(ogr.FieldDefn("color", ogr.OFTString))
        src_band = src_ds.GetRasterBand(1)

        # (srcBand, maskBand, outLayer, iPixValField)
        gdal.Polygonize(src_band, None, dst_layer, 0)

        src_ds = None  # close dataset
        dst_ds = None  # close dataset

        with open(outfile_name, "rb") as f:
            fc = geojson.load(f)
            return transform(fc)
