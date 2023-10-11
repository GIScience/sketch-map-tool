from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from osgeo import gdal, ogr, osr


def reproject_geojson(
    layer_name,
    srs_srs,
    outfile_name: str,
    reprojected_name: str,
) -> None:
    """Reproject GeoJSON from WebMercator to EPSG:4326"""
    # create transformation
    out_spatial_ref = osr.SpatialReference()
    out_spatial_ref.ImportFromEPSG(4326)
    coord_trans = osr.CreateCoordinateTransformation(srs_srs, out_spatial_ref)

    # load/create in and reprojected layers
    driver = ogr.GetDriverByName("GeoJSON")
    in_data_set = driver.Open(outfile_name)
    in_layer = in_data_set.GetLayer()

    reproj_ds = driver.CreateDataSource(reprojected_name)
    reproj_layer = reproj_ds.CreateLayer(layer_name, srs=out_spatial_ref)
    reproj_layer_definition = reproj_layer.GetLayerDefn()

    # loop though features in input, reproject and write to output
    in_feature = in_layer.GetNextFeature()
    while in_feature:
        geom = in_feature.GetGeometryRef()

        geom.Transform(coord_trans)

        out_feature = ogr.Feature(reproj_layer_definition)
        out_feature.SetGeometry(geom)
        reproj_layer.CreateFeature(out_feature)

        out_feature = None
        in_feature = in_layer.GetNextFeature()
    reproj_ds = None
    in_data_set = None


def polygonize(geotiff: BytesIO, layer_name: str) -> BytesIO:
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
        reprojected_name = Path(tmpdirname) / "reprojected.geojson"

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

        reproject_geojson(layer_name, srs, str(outfile_name), str(reprojected_name))

        with open(reprojected_name, "rb") as f:
            return BytesIO(f.read())
