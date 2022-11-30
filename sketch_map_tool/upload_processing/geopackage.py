from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import geojson
from geojson import FeatureCollection
from osgeo import ogr, osr

from sketch_map_tool.definitions import COLORS


def geopackage(fcs: list[FeatureCollection]) -> BytesIO:
    # fc  -> feature collection
    # fcs -> feature collections (multiple)
    with TemporaryDirectory() as tmpdirname:
        outfile = str(Path(tmpdirname) / "out.gpkg")
        infile = str(Path(tmpdirname) / "in.geojson")

        # open geopackage
        driver = ogr.GetDriverByName("GPKG")
        dst_ds = driver.CreateDataSource(outfile)

        for fc, color in zip(fcs, COLORS):
            with open(infile, "w") as file:
                geojson.dump(fc, file)

            src_ds = ogr.Open(infile)
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
        with open(outfile, "rb") as f:
            return BytesIO(f.read())
