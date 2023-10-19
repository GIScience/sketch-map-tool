from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray
from reportlab.graphics.shapes import Drawing


def get_project_root() -> Path:
    """Get root of the Python project."""
    return Path(__file__).resolve().parent.parent.resolve()


def resize_rlg_by_width(d: Drawing, size: float) -> Drawing:
    factor = size / d.width
    d.scale(factor, factor)
    d.asDrawing(d.width * factor, d.height * factor)
    return d


def resize_rlg_by_height(d: Drawing, size: float) -> Drawing:
    factor = size / d.height
    d.scale(factor, factor)
    d.asDrawing(d.width * factor, d.height * factor)
    return d


def to_array(buffer: bytes) -> NDArray:
    return cv2.imdecode(np.frombuffer(buffer, dtype="uint8"), cv2.IMREAD_UNCHANGED)
