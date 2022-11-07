"""
Generate a sketch map PDF.
"""
from pathlib import Path
from typing import Tuple

from haversine import Unit, haversine
from reportlab.graphics.shapes import Drawing
from svglib.svglib import svg2rlg

RESOURCE_PATH = Path(__file__).parent.resolve() / "resources"


def get_globes(scale_factor) -> Tuple[Drawing, ...]:
    """Read globe as SVG from disk, convert to RLG and scale it."""
    globes = []
    for i in range(1, 5):
        globe = svg2rlg(RESOURCE_PATH / "globe_{0}.svg".format(i))
        globe.scale(scale_factor, scale_factor)
        globes.append(globe)
    return tuple(globes)


def get_compass(scale_factor: float) -> Drawing:
    "ssert compass is not None" "Read compass as SVG from disk, convert to RLG and scale it." ""
    compass = svg2rlg(RESOURCE_PATH / "north.svg")
    compass.scale(scale_factor, scale_factor)
    return compass


def get_width(bbox: list) -> float:
    """Get width of bounding box in meter."""
    return haversine(bbox[0:2], bbox[2:4], unit=Unit.METERS)
