"""
Read QR codes from photos / scans
"""

from typing import Any

import cv2
import numpy as np
from pyzbar import pyzbar


class NoQRCodeException(Exception):
    """
    Exception to indicate that no QR code could be detected on a given image.
    """

    def __init__(self) -> None:
        super().__init__("No QR code could be detected on the image")


class MultipleDifferentQRCodesException(Exception):
    """
    Exception to indicate that multiple QR codes with different contents have been detected on a
    given image, making it unclear which contents should be used.
    """

    def __init__(self) -> None:
        super().__init__(
            "Multiple QR codes with different contents have been detected on the image"
        )


def read(image: "np.ndarray[Any, np.dtype[np.int64]]") -> str:
    """
    :param image: Image containing one QR code.
    :return: Contents of the QR code.
    :raises NoQRCodeException: If no code is found.
    :raises MultipleDifferentQRCodes: In case there are multiple QR codes with different contents
                                      on the photo.
    """
    height, width, _ = image.shape

    # Downscale in case of large resolutions because pyzbar has problems otherwise:
    if height > 2000 or width > 2000:
        if height > width:
            scaling_factor = 2000 / height
        else:
            scaling_factor = 2000 / width
        image = cv2.resize(
            image, (int(scaling_factor * width), int(scaling_factor * height))
        )

    decoded_objects = pyzbar.decode(image)
    if len(decoded_objects) == 0:
        raise NoQRCodeException
    first_code_contents = str(decoded_objects[0].data.decode())
    if len(decoded_objects) > 1:
        for dec_object in decoded_objects:
            if str(dec_object.data.decode()) != first_code_contents:
                raise MultipleDifferentQRCodesException
    return first_code_contents
