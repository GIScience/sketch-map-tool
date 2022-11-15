"""
Read QR codes from photos / scans
"""

from typing import Any

import cv2
import numpy as np
from pyzbar import pyzbar

from sketch_map_tool.exceptions import QRCodeError


def read(img: "np.ndarray[Any, np.dtype[np.int64]]", depth=0) -> str:
    """Detect and decode QR-Code.

    If QR-Code is falsely detected but no data exists recursively down scale QR-Code
    image until data exists or maximal recursively depth is reached.

    :param image: Image containing one QR code.
    :param depth: Maximal recursion depth
    :return: Contents of the QR code.
    :raises QRCodeError: If no QR-code could be detected or if multiple QR-codes have
        been detected.
    """
    decoded_objects = pyzbar.decode(img)

    match len(decoded_objects):
        case 0:
            if depth <= 5:
                # Try again with down scaled image
                read(_resize(img), depth=depth + 1)
            else:
                raise QRCodeError("QR-Code could not be detected.")
        case 1:
            return decoded_objects[0].data.decode()
        case _:
            raise QRCodeError("Multiple QR-Codes detected.")


def _resize(img, scale: float = 0.75):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    # resize image
    return cv2.resize(img, (width, height))
