"""Web Map Service Client"""

from typing import List

import requests
from PIL import Image
from PIL.PngImagePlugin import PngImageFile
from requests import Response

from sketch_map_tool.config import get_config_value


# TODO: request errors in a response format which can be parsed.
# Currently errors are rendered into the image.
def get_map_image(bbox: List[float], width: float, height: float) -> Response:
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
        "WIDTH": width,
        "HEIGHT": height,
        "SRS": "EPSG:3857",
        "STYLES": "",
        "BBOX": ",".join([str(cord) for cord in bbox]),
    }
    return requests.get(url, params, stream=True, timeout=50)


def as_image(response: Response) -> PngImageFile:
    return Image.open(response.raw)
