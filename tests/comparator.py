from pathlib import Path

import geopandas
from approvaltests.core import FileComparator


class GeoJSONComparator(FileComparator):
    def compare(self, received_path: str, approved_path: str) -> bool:
        if not Path(approved_path).exists() or Path(approved_path).stat().st_size == 0:
            return False

        # EPSG:8857 - small scale equal-area mapping
        df_received = geopandas.read_file(received_path).to_crs("EPSG:8857")
        df_approved = geopandas.read_file(approved_path).to_crs("EPSG:8857")

        if len(df_approved) != len(df_received):
            return False

        area_clipped = df_received.clip(df_approved).area
        area_diff = df_approved.area - area_clipped
        area_ratio = area_diff / df_approved.area
        for r in area_ratio:
            if r > 0.01:
                return False
        return True
