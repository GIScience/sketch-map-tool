"""Web Map Service Client"""

from dataclasses import astuple
from io import BytesIO

import requests
from markupsafe import escape
from PIL import Image, UnidentifiedImageError
from PIL.PngImagePlugin import PngImageFile
from requests import ReadTimeout, Response

from sketch_map_tool.config import get_config_value
from sketch_map_tool.exceptions import MapGenerationError
from sketch_map_tool.models import Bbox, Layer, Size


# TODO: request errors in a response format which can be parsed.
# Currently errors are rendered into the image.
def get_map_image(
    bbox: Bbox,
    size: Size,
    layer: Layer,
) -> Response:
    """Request a map image from the given WMS with the given arguments."""
    url = get_config_value(f"wms-url-{layer.value}")
    layers = get_config_value(f"wms-layers-{layer.value}")
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
        return requests.get(
            url,
            params,
            stream=True,
            # connect timeout (5 seconds), read_timeout (10 minutes)
            timeout=(10, int(get_config_value("wms-read-timeout"))),
        )
    except ReadTimeout:
        raise MapGenerationError(
            "Map area couldn't be processed with the current resources."
            " Please try again once."
        )


def as_image(response: Response) -> PngImageFile:
    response_content = response.content
    content_type = response.headers["content-type"]
    response.close()
    try:
        return Image.open(BytesIO(response_content))
    except UnidentifiedImageError:
        error_msg = "The Web Map Service returned an error. Please try again later."

        if (
            content_type == "application/vnd.ogc.se_xml"
        ):  # Response is an XML error report
            error_msg += " Response from the WMS:\n" + escape(
                response_content.decode("utf8")
            )
        raise MapGenerationError(error_msg)
