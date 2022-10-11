"""
Instances representing all possible paper formats in the sketch map tool
"""

from typing import Tuple, Optional


class PaperFormat:  # pylint: disable=R0903
    """
    Properties of sketch maps to be printed on a certain paper format
    """

    def __init__(self,
                 title: str,
                 width: float,
                 height: float,
                 right_margin: float,
                 font_size: int,
                 qr_scale: float,
                 compass_scale: float,
                 globe_scale: float,
                 scale_height: float,
                 qr_y: float,
                 indent: float,
                 qr_contents_distances_not_rotated: Tuple[int, int],
                 qr_contents_distance_rotated: int,
                 ):  # pylint: disable=R0913
        """
        :param title: Name of the paper format
        :param width: Width of the paper in cm.
        :param height: Height of the paper in cm.
        :param right_margin: Width of the margin in cm, i.e. the area not covered by the map
                             containing the QR code, scale, copyright information, etc.
        :param font_size: Font size in pt to be used for the copyright info and code contents.
        :param qr_scale: Scale factor for the QR code SVG.
        :param compass_scale: Scale factor for the compass SVG.
        :param globe_scale: Scale factor for the globe SVGs.
        :param scale_height: Height of the scale in cm, the width is calculated according to the
                             actual size of the bounding box and its size on the map.
        :param qr_y: Vertical distance from the QR code to the origin in cm.
        :param indent: Indentation in cm of the contents in the margin relative to the map area.
        :param qr_contents_distances_not_rotated: (Vertical distance in cm from the qr code contents
                                                   in text form to the position of the copyright
                                                   notice, Indentation in cm additional to the
                                                   calculated base indentation of all rotated
                                                   contents).
        :param qr_contents_distance_rotated: Horizontal distance in cm from the map area additional
                                             to the calculated base indentation of all rotated
                                             contents.
        """
        self.title = title
        self.width = width
        self.height = height
        self.right_margin = right_margin
        self.font_size = font_size
        self.qr_scale = qr_scale
        self.compass_scale = compass_scale
        self.globe_scale = globe_scale
        self.scale_height = scale_height
        self.qr_y = qr_y
        self.indent = indent
        self.qr_contents_distances_not_rotated = qr_contents_distances_not_rotated
        self.qr_contents_distance_rotated = qr_contents_distance_rotated

    @staticmethod
    def from_str(paper_format_str: str) -> "Optional[PaperFormat]":
        """
        Get a paper format object based on the name of it's format

        :return: PaperFormat object in case the name is known, otherwise None
        """
        return {
            "a0": A0,
            "a1": A1,
            "a2": A2,
            "a3": A3,
            "a4": A4,
            "a5": A5,
            "legal": LEGAL,
            "tabloid": TABLOID,
            "ledger": LEDGER,
            "letter": LETTER,
        }.get(paper_format_str.lower().strip(), None)

    def __str__(self) -> str:
        """
        Get the name of the paper format.

        :return: 'title' attribute of the paper format.
        """
        return self.title


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

LEDGER = PaperFormat(
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
