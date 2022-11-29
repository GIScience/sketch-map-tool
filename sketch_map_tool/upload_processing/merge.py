from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from osgeo import ogr, osr

from sketch_map_tool.definitions import COLORS


def merge(geojsons: list) -> BytesIO:
    with TemporaryDirectory() as tmpdirname:
        outfile_name = str(Path(tmpdirname) / "out.geojson")

        # open geopackage
        driver = ogr.GetDriverByName("GPKG")
        dst_ds = driver.CreateDataSource(outfile_name)

        for geojson, color in zip(geojsons, COLORS):
            infile = NamedTemporaryFile()
            with open(infile.name, "wb") as f:
                f.write(geojson.getbuffer())

            src_ds = ogr.Open(infile.name)
            src_layer = src_ds.GetLayer()

            srs = osr.SpatialReference()
            srs.ImportFromEPSG(3857)  # WGS 84 / Pseudo-Mercator

            dst_layer = dst_ds.CreateLayer(color, srs)
            for feat in src_layer:
                dst_feat = ogr.Feature(dst_layer.GetLayerDefn())
                dst_feat.SetGeometry(feat.GetGeometryRef().Clone())
                dst_layer.CreateFeature(dst_feat)
                dst_feat = None
                dst_layer.SyncToDisk()
        src_ds = None  # close dataset
        dst_ds = None  # close dataset
        with open(outfile_name, "rb") as f:
            return BytesIO(f.read())
