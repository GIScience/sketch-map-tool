"""
Read QR codes from photos / scans
"""
import json
from types import MappingProxyType

import cv2
from numpy.typing import NDArray
from pyzbar import pyzbar

from sketch_map_tool.exceptions import QRCodeError
from sketch_map_tool.helpers import N_
from sketch_map_tool.models import Bbox, Layer
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
                raise QRCodeError(N_("QR-Code could not be detected."))
        case 1:
            try:
                data = _decode_data(decoded_objects[0].data.decode())
            except QRCodeError:
                data = _decode_data_legacy(decoded_objects[0].data.decode())
            try:
                validate_uuid(data["uuid"])
            except ValueError:
                raise QRCodeError(N_("The provided UUID is invalid."))
            return data
        case _:
            raise QRCodeError(N_("Multiple QR-Codes detected."))


def _decode_data(data) -> MappingProxyType:
    try:
        contents = data.split(",")
        if len(contents) == 6:
            # Legacy support (before satellite imagery feature)
            contents.append(Layer("osm"))
        if not len(contents) == 7:  # version nr, uuid, bbox coordinates and layer
            raise ValueError(N_("Unexpected length of QR-code contents."))
        version_nr = contents[0]
        uuid = contents[1]
        bbox = Bbox(
            *[float(coordinate) for coordinate in contents[2:-1]]
        )  # Raises ValueError for non-float values
        try:
            layer = getattr(Layer, (contents[7]))
        except IndexError:
            # backward compatibility
            layer = getattr(Layer, "OSM")
    except ValueError as error:
        raise QRCodeError(N_("QR-Code does not have expected content.")) from error
    return MappingProxyType(
        {
            "uuid": uuid,
            "bbox": bbox,
            "version": version_nr,
            "layer": layer,
        }
    )


def _decode_data_legacy(data) -> MappingProxyType:
    try:
        contents = json.loads(data)
        uuid = contents["id"]
        version_nr = contents["version"]
        bbox = Bbox(
            *[float(coordinate) for coordinate in contents["bbox"].values()]
        )  # Raises ValueError for non-float values
        layer = Layer("osm")
    except ValueError as error:
        raise QRCodeError(N_("QR-Code does not have expected content.")) from error
    return MappingProxyType(
        {
            "uuid": uuid,
            "bbox": bbox,
            "version": version_nr,
            "layer": layer,
        }
    )


def _resize(img, scale: float = 0.75):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    # resize image
    return cv2.resize(img, (width, height))
