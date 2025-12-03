import logging
from pathlib import Path

import geopandas
import numpy as np
from approvaltests.core import FileComparator
from PIL import Image


class GeoJSONComparator(FileComparator):
    def compare(self, received_path: str, approved_path: str) -> bool:
        if not Path(approved_path).exists() or Path(approved_path).stat().st_size == 0:
            return False

        # EPSG:8857 - small scale equal-area mapping
        # TODO: Maybe EPSG 3857 is better/enough?
        df_received = geopandas.read_file(received_path).to_crs("EPSG:8857")
        df_approved = geopandas.read_file(approved_path).to_crs("EPSG:8857")

        df_received_points = df_received[df_received.geometry.type == "Point"]
        df_approved_points = df_approved[df_approved.geometry.type == "Point"]

        df_approved_polygons = df_approved[df_approved.geometry.type == "Polygon"]
        df_received_polygons = df_received[df_received.geometry.type == "Polygon"]

        if len(df_approved_polygons.index) != len(df_received_polygons.index):
            logging.warning("Different number of polygon features detected.")
            return False

        if len(df_approved_points.index) != len(df_received_points.index):
            logging.warning("Different number of point features detected.")
            return False

        # NOTE: Hausdorff distance might be better to determine similarity
        area_diff = df_received_polygons.symmetric_difference(df_approved_polygons).area
        area_union = df_received_polygons.union(df_approved_polygons).area
        diff = area_diff / area_union
        for d in diff.tolist():
            if d > 0.1:
                logging.warning(f"Area differs by more than {d:.0%}")
                return False
        return True


class ImageComparator(FileComparator):
    def compare(self, received_path: str, approved_path: str) -> bool:
        if not Path(approved_path).exists() or Path(approved_path).stat().st_size == 0:
            return False
        image_received = Image.open(received_path)
        image_approved = Image.open(approved_path)
        return (np.array(image_received) == np.array(image_approved)).all()
