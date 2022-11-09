"""Paper format specifications"""

from dataclasses import dataclass
from typing import Tuple


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
    qr_contents_distances_not_rotated: Tuple[int, int]
    qr_contents_distance_rotated: int


A0 = PaperFormat(
    "a0",
    width=118.9,
    height=84.1,
    right_margin=15,
    font_size=25,
    qr_scale=3.5,
    compass_scale=1,
    globe_scale=0.5,
    scale_height=1,
    qr_y=0.5,
    indent=0.5,
    qr_contents_distances_not_rotated=(10, 10),
    qr_contents_distance_rotated=10,
)
A1 = PaperFormat(
    "a1",
    width=84.1,
    height=59.4,
    right_margin=12,
    font_size=20,
    qr_scale=2.5,
    compass_scale=0.75,
    globe_scale=0.375,
    scale_height=1,
    qr_y=0.5,
    indent=0.5,
    qr_contents_distances_not_rotated=(5, 8),
    qr_contents_distance_rotated=7,
)
A2 = PaperFormat(
    "a2",
    width=59.4,
    height=42,
    right_margin=7.5,
    font_size=12,
    qr_scale=1.75,
    compass_scale=0.5,
    globe_scale=0.25,
    scale_height=0.75,
    qr_y=0.5,
    indent=0.5,
    qr_contents_distances_not_rotated=(6, 4),
    qr_contents_distance_rotated=4,
)
A3 = PaperFormat(
    "a3",
    width=42,
    height=29.7,
    right_margin=7,
    font_size=11,
    qr_scale=1.5,
    compass_scale=0.33,
    globe_scale=0.165,
    scale_height=0.5,
    qr_y=0.5,
    indent=0.5,
    qr_contents_distances_not_rotated=(3, 4),
    qr_contents_distance_rotated=4,
)
A4 = PaperFormat(
    "a4",
    width=29.7,
    height=21,
    right_margin=5,
    font_size=8,
    qr_scale=1,
    compass_scale=0.25,
    globe_scale=0.125,
    scale_height=0.33,
    qr_y=0.1,
    indent=0.25,
    qr_contents_distances_not_rotated=(2, 3),
    qr_contents_distance_rotated=3,
)
A5 = PaperFormat(
    "a5",
    width=21,
    height=14.8,
    right_margin=3,
    font_size=5,
    qr_scale=0.75,
    compass_scale=0.2,
    globe_scale=0.1,
    scale_height=0.25,
    qr_y=0.1,
    indent=0.1,
    qr_contents_distances_not_rotated=(2, 2),
    qr_contents_distance_rotated=2,
)
LEGAL = PaperFormat(
    "legal",
    width=35.6,
    height=21.6,
    right_margin=5,
    font_size=8,
    qr_scale=1,
    compass_scale=0.25,
    globe_scale=0.125,
    scale_height=0.33,
    qr_y=0.1,
    indent=0.25,
    qr_contents_distances_not_rotated=(2, 3),
    qr_contents_distance_rotated=3,
)
TABLOID = PaperFormat(
    "tabloid",
    width=43.2,
    height=27.9,
    right_margin=7,
    font_size=11,
    qr_scale=1.5,
    compass_scale=0.33,
    globe_scale=0.165,
    scale_height=0.5,
    qr_y=0.01,
    indent=0.5,
    qr_contents_distances_not_rotated=(3, 4),
    qr_contents_distance_rotated=4,
)
LETTER = PaperFormat(
    "letter",
    width=27.9,
    height=21.6,
    right_margin=5,
    font_size=8,
    qr_scale=1,
    compass_scale=0.25,
    globe_scale=0.125,
    scale_height=0.33,
    qr_y=0.1,
    indent=0.25,
    qr_contents_distances_not_rotated=(2, 3),
    qr_contents_distance_rotated=3,
)
