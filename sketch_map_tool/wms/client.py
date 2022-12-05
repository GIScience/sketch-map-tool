"""Web Map Service Client"""

from dataclasses import astuple

import requests
from PIL import Image
from PIL.PngImagePlugin import PngImageFile
from requests import ReadTimeout, Response

from sketch_map_tool.config import get_config_value
from sketch_map_tool.exceptions import MapGenerationError
from sketch_map_tool.models import Bbox, Size


# TODO: request errors in a response format which can be parsed.
# Currently errors are rendered into the image.
def get_map_image(bbox: Bbox, size: Size) -> Response:
    """Request a map image from the given WMS with the given arguments.

    :param bbox: Bounding box (EPSG: 3857)
    :param width: Width in pixels
    :param height: Height in pixels
    """
    url = get_config_value("wms-url")
    layers = get_config_value("wms-layers")
    params = {
        "REQUEST": "GetMap",
        "FORMAT": "image/png",
        "TRANSPARENT": "FALSE",
        "LAYERS": layers,
        "WIDTH": size.width,
        "HEIGHT": size.height,
        "SRS": "EPSG:3857",
        "STYLES": "",
        "BBOX": ",".join([str(cord) for cord in astuple(bbox)]),
    }
    try:
        return requests.get(url, params, stream=True, timeout=600)
    except ReadTimeout:
        raise MapGenerationError(
            "Map area couldn't be processed with the current resources. Please try again once."
        )


def as_image(response: Response) -> PngImageFile:
    return Image.open(response.raw)
