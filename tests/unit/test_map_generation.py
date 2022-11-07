from dataclasses import dataclass
from typing import Tuple

from reportlab.graphics.shapes import Drawing

from sketch_map_tool.map_generation import generate_pdf


# TODO: Remove once paper_format is implemented
@dataclass(frozen=True)
class PaperFormat:
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


def test_get_globes():
    globes = generate_pdf.get_globes(A4.globe_scale)
    for globe in globes:
        assert isinstance(globe, Drawing)


def test_get_compass():
    compass = generate_pdf.get_compass(A4.compass_scale)
    assert isinstance(compass, Drawing)


def test_get_width():
    bbox = (8.66100311, 49.3957813, 8.71662140, 49.4265373)
    width = generate_pdf.get_width(bbox)
    assert width == 7048.170206241312  # TODO: verify
