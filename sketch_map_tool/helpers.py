from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image as PILImage
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
    return cv2.imdecode(np.fromstring(buffer, dtype="uint8"), cv2.IMREAD_UNCHANGED)


def resize_png(input_buffer: BytesIO, max_length: float) -> BytesIO:
    input_img = PILImage.open(input_buffer)
    ratio = input_img.width / input_img.height
    if ratio > 1:
        width = min(max_length, input_img.width)
        height = width / ratio
    else:
        height = min(max_length, input_img.height)
        width = height * ratio
    output_image = BytesIO()
    input_img.resize((int(width), int(height))).save(output_image, format="png")
    output_image.seek(0)
    return output_image
