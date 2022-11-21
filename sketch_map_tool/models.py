import os
from dataclasses import dataclass

from werkzeug.utils import secure_filename


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


@dataclass(frozen=True)
class PaperFormat:
    """Properties of sketch maps to be printed on a certain paper format.

    Attributes:
        title: Name of the paper format
        width: Width of the paper [cm]
        height: Height of the paper [cm]
        right_margin: Width of the margin [cm]
        font_size: Font size [pt]
        qr_scale: Scale factor of the QR-code
        compass_scale: Scale factor of the compass
        globe_scale: Scale factor of the globes
        scale_height: Height of the scale [cm].
            The width is calculated in proportion to the map (bounding box).
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
    font_size: int
    qr_scale: float
    compass_scale: float
    globe_scale: float
    scale_height: float
    qr_y: float
    indent: float
    qr_contents_distances_not_rotated: tuple[int, int]
    qr_contents_distance_rotated: int


@dataclass()
class LiteratureReference:
    citation: str
    img_src: str | None = None
    url: str | None = None

    def __post_init__(self):
        # if image is stored on disk
        if self.img_src is not None and not self.img_src.strip().startswith("http"):
            self.img_src = os.path.join(
                "assets",
                "images",
                "about",
                "publications",
                secure_filename(self.img_src),
            )
