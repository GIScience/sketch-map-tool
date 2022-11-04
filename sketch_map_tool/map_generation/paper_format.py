"""Paper format specifications"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PaperFormat:
    """Properties of sketch maps to be printed on a certain paper format.

    :param title: Name of the paper format
    :param width: Width of the paper in cm.
    :param height: Height of the paper in cm.
    :param right_margin: Width of the margin in cm.
    :param font_size: Font size in pt.
    :param qr_scale: Scale factor of the QR code int SVG format.
    :param compass_scale: Scale factor of the compass in SVG format.
    :param globe_scale: Scale factor of the globes in SVG format.
    :param scale_height: Height of the scale in cm.
        The width is calculated in proportion to the map (bounding box).
    :param qr_y: Vertical distance in cm from the QR code to the origin.
    :param indent: Indentation in cm of the margins content relative to the map area.
    :param qr_contents_distances_not_rotated:
        (Vertical distance in cm from the qr code contents in text form to the position
        of the copyright notice, Indentation in cm additional to the calculated base
        indentation of all rotated contents)
    :param qr_contents_distance_rotated:
        Horizontal distance in cm from the map area additional to the calculated base
        indentation of all rotated contents.
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


def paper_format(format_: str) -> PaperFormat:
    """Initiates a `PaperFormat` object with the appropriate properties of the given format"""
    match format_.upper():
        case "A0":
            return PaperFormat(
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
        case "A1":
            return PaperFormat(
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
        case "A2":
            return PaperFormat(
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
        case "A3":
            return PaperFormat(
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
        case "A4":
            return PaperFormat(
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
        case "A5":
            return PaperFormat(
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
        case "LEGAL":
            return PaperFormat(
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
        case "TABLOID":
            return PaperFormat(
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
        case "LEDGER":
            return PaperFormat(
                "ledger",
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
        case "LETTER":
            return PaperFormat(
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
