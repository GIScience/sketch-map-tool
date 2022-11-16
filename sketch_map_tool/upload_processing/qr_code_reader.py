"""
Read QR codes from photos / scans
"""

import json
from json import JSONDecodeError
from types import MappingProxyType
from typing import Any

import cv2
import numpy as np
from pyzbar import pyzbar

from sketch_map_tool import definitions
from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.models import Bbox, Size


def read(img: "np.ndarray[Any, np.dtype[np.int64]]", depth=0) -> MappingProxyType:
    """Detect and decode QR-Code.

    If QR-Code is falsely detected but no data exists recursively down scale QR-Code
    image until data exists or maximal recursively depth is reached.

    :param image: Image containing one QR code.
    :param depth: Maximal recursion depth
    :return: Contents of the QR-Code.
    :raises QRCodeError: If no QR-Code could be detected
        or if multiple QR-Codes have been detected
        or if QR-Code does not have expected content
    """
    decoded_objects: list = pyzbar.decode(img)
    match len(decoded_objects):
        case 0:
            if depth <= 5:
                # Try again with down scaled image
                read(_resize(img), depth=depth + 1)
            else:
                raise QRCodeError("QR-Code could not be detected.")
        case 1:
            data = decoded_objects[0].data.decode()
            return _decode_data(data)
        case _:
            raise QRCodeError("Multiple QR-Codes detected.")


def _decode_data(data) -> MappingProxyType:
    try:
        d = json.loads(data)
    except JSONDecodeError as error:
        raise QRCodeError("QR-Code does not have expected content.") from error
    try:
        return MappingProxyType(
            {
                "uuid": d["id"],
                "bbox": Bbox(**d["bbox"]),
                "format_": getattr(definitions, d["format"].upper()),
                "orientation": d["orientation"],
                "size": Size(**d["size"]),
            }
        )
    except KeyError as error:
        raise QRCodeError("QR-Code does not have expected content.") from error


def _resize(img, scale: float = 0.75):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    # resize image
    return cv2.resize(img, (width, height))
