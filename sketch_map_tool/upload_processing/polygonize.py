from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from osgeo import gdal, ogr, osr


def polygonize(geotiff: BytesIO, layer_name: str) -> BytesIO:
    """Produces a polygon feature layer (GeoJSON) from a raster (GeoTIFF)."""
    gdal.UseExceptions()
    ogr.UseExceptions()

    # open geotiff
    infile = NamedTemporaryFile(suffix=".geotiff")
    with open(infile.name, "wb") as f:
        f.write(geotiff.getbuffer())
    src_ds = gdal.Open(infile.name)
    srs = osr.SpatialReference(wkt=src_ds.GetProjection())

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
            return BytesIO(f.read())
