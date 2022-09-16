"""
Retrieve a map image from a Web Map Service
(see https://wiki.openstreetmap.org/wiki/WMS for further information on WMS)
"""
from constants import WMS_BASE_URL, WMS_LAYERS, TIMEOUT_REQUESTS
from helper_modules.bbox_utils import Bbox
from PIL import Image
import requests


def get_map_image(bbox: Bbox, height_px: int, width_px: int,
                  wms_service_base_url: str = WMS_BASE_URL, wms_layers: str = WMS_LAYERS) -> Image:
    """
    Request a map image from the given WMS with the given arguments.

    :param bbox: Bounding box of which the map should be generated (WGS 84).
    :param height_px: Height in pixels of the requested map image.
    :param width_px: Width in pixels of the requested map image.
    :wms_service_base_url: Base URL of the WMS of which the map is requested.
    :wms_layers: Requested layer(s) from the WMS
    """
    params = {
        "REQUEST": "GetMap",
        "FORMAT": "image%2Fpng",
        "TRANSPARENT": "FALSE",
        "LAYERS": wms_layers,
        "WIDTH": width_px,
        "HEIGHT": height_px,
        "SRS": "EPSG%3A4326",
        "STYLES": "",
        "BBOX": bbox.get_str(mode="comma")
    }
    return Image.open(
        requests.get(wms_service_base_url, params, stream=True, timeout=TIMEOUT_REQUESTS).raw
    )
