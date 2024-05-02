from pathlib import Path

import geopandas
from approvaltests.core import FileComparator


class GeoJSONComparator(FileComparator):
    def compare(self, received_path: str, approved_path: str) -> bool:
        if not Path(approved_path).exists() or Path(approved_path).stat().st_size == 0:
            return False

        # TODO: find optimal UTM for every feature or different projection
        df_received = geopandas.read_file(received_path).to_crs("EPSG:32632")
        df_approved = geopandas.read_file(approved_path).to_crs("EPSG:32632")

        if len(df_approved) != len(df_received):
            return False

        area_clipped = df_received.clip(df_approved).area
        area_diff = df_approved.area - area_clipped
        area_ratio = area_diff / df_approved.area
        for r in area_ratio:
            # TODO: what is the right threshold
            if r > 0.01:
                return False
        return True
