from dataclasses import dataclass


@dataclass(frozen=True)
class Bbox:
    """Bounding Box in WGS 84 / Pseudo-Mercator (EPSG:3857)"""

    lat_min: float
    lon_min: float
    lat_max: float
    lon_max: float


@dataclass(frozen=True, kw_only=True)
class Size:
    """Print box size in dots [pt].

    This is useful to determine the OGC-WMS params 'WIDTH' and 'HEIGHT'.
    """

    width: float
    height: float
