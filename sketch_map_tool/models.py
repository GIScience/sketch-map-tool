from dataclasses import dataclass
from enum import StrEnum

from numpy.typing import NDArray


@dataclass(frozen=True)
class Bbox:
    """Bounding Box in WGS 84 / Pseudo-Mercator (EPSG:3857)

    Be aware that the argument order is relevant to the API and the JavaScript client.
    Keep the order in sync with the client.
    """

    lon_min: float
    lat_min: float
    lon_max: float
    lat_max: float

    @property
    def centroid(self) -> tuple:
        """The coordinates of the centroid."""
        lon_centroid = (self.lon_min + self.lon_max) / 2
        lat_centroid = (self.lat_min + self.lat_max) / 2
        return (lon_centroid, lat_centroid)

    def __str__(self):
        # NOTE: this should probably be a WKT representation
        return f"{self.lon_min},{self.lat_min},{self.lon_max},{self.lat_max}"


@dataclass(frozen=True, kw_only=True)
class Size:
    """Print box size in dots [pt].

    This is useful to determine the OGC-WMS params 'WIDTH' and 'HEIGHT'.
    """

    width: float
    height: float


class Layer(StrEnum):
    OSM = "osm"
    ESRI_WORLD_IMAGERY = "esri-world-imagery"
    ESRI_WORLD_IMAGERY_FALLBACK = "esri-world-imagery-fallback"


@dataclass(frozen=True)
class PaperFormat:
    """Properties of sketch maps to be printed on a certain paper format.

    Attributes:
        title: Name of the paper format
        width: Width of the paper [cm]
        height: Height of the paper [cm]
        right_margin: Width of the margin [cm]
        map_margin: Width of the margin around the map [cm]
        font_size: Font size [pt]
        qr_scale: Scale factor of the QR-code
        compass_scale: Scale factor of the compass
        marker_scale: Scale factor of the aruco markers
        scale_height: Height of the scale [px].
        scale_relative_xy: Position of the scale relative to the map frame width or
            height respectively
        scale_background_params: (x relative to scale, y relative to scale,
            length additional to scale, height)
        scale_distance_to_text: Distance from the scale bar
            to the text describing it [px]
        qr_y: Vertical distance from origin to the QR-code [cm]
        indent: Indentation of the margin's content relative to the map area [cm]
        qr_contents_distances_not_rotated: Tuple of distances [cm]
            (Vertical distance from the QR-code contents in text form to the position
            of the copyright notice, Indentation additional to the calculated base
            indentation of all rotated contents)
        qr_contents_distance_rotated:
            Horizontal distance from the map area additional to the calculated base
            indentation of all rotated contents [cm]
    """

    title: str
    width: float
    height: float
    right_margin: float
    map_margin: float
    font_size: int
    qr_scale: float
    compass_scale: float
    marker_scale: float
    scale_height: int
    scale_relative_xy: tuple[int, int]
    scale_background_params: tuple[int, int, int, int]
    scale_distance_to_text: int
    qr_y: float
    indent: float
    qr_contents_distances_not_rotated: tuple[int, int]
    qr_contents_distance_rotated: int

    def __str__(self):
        return self.title


@dataclass()
class LiteratureReference:
    citation: str
    img_src: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class File:
    filename: str
    mimetype: str
    image: NDArray
