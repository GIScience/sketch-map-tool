"""
Read QR codes from photos / scans
"""

from types import MappingProxyType

import cv2
from numpy.typing import NDArray
from pyzbar import pyzbar

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.models import Bbox
from sketch_map_tool.validators import validate_uuid


def read(img: NDArray, depth=0) -> MappingProxyType:
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
                return read(_resize(img), depth=depth + 1)
            else:
                raise QRCodeError("QR-Code could not be detected.")
        case 1:
            data = _decode_data(decoded_objects[0].data.decode())
            try:
                validate_uuid(data["uuid"])
            except ValueError:
                raise QRCodeError("The provided UUID is invalid.")
            return data
        case _:
            raise QRCodeError("Multiple QR-Codes detected.")


def _decode_data(data) -> MappingProxyType:
    try:
        contents = data.split(",")
        if not len(contents) == 6:  # version nr, uuid and bbox coordinates
            raise ValueError("Unexpected length of QR-code contents.")
        version_nr = contents[0]
        uuid = contents[1]
        bbox = Bbox(
            *[float(coordinate) for coordinate in contents[2:]]
        )  # Raises ValueError for non-float values
    except ValueError as error:
        raise QRCodeError("QR-Code does not have expected content.") from error
    return MappingProxyType({"uuid": uuid, "bbox": bbox, "version": version_nr})


def _resize(img, scale: float = 0.75):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    # resize image
    return cv2.resize(img, (width, height))
