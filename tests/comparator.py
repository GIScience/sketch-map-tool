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

        if len(df_approved.index) != len(df_received.index):
            print("Different numbers of features detected.")
            return False

        # NOTE: Hausdorff distance might be better to determine similarity
        area_diff = df_received.symmetric_difference(df_approved).area
        area_union = df_received.union(df_approved).area
        diff = area_diff / area_union
        for d in diff.tolist():
            if d > 0.05:
                print("Area differs more than 5%.")
                return False
        return True


class ImageComparator(FileComparator):
    def compare(self, received_path: str, approved_path: str) -> bool:
        if not Path(approved_path).exists() or Path(approved_path).stat().st_size == 0:
            return False
        image_received = Image.open(received_path)
        image_approved = Image.open(approved_path)
        return (np.array(image_received) == np.array(image_approved)).all()
