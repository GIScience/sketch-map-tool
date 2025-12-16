from dataclasses import astuple
from io import BytesIO
from typing import Literal

import requests
from markupsafe import escape
from PIL import Image, UnidentifiedImageError
from requests import ReadTimeout, Response

from sketch_map_tool.config import CONFIG
from sketch_map_tool.exceptions import MapGenerationError
from sketch_map_tool.helpers import N_
from sketch_map_tool.models import Bbox, Size


def get_map_image(
    bbox: Bbox,
    size: Size,
    layer: str,
) -> Image.Image:
    """Get a map image from the WMS."""
    if layer == "esri-world-imagery":
        format = "jpeg"
    else:
        format = "png"
    response = get_map(bbox, size, layer, format)
    try:
        image = as_image(response, format)
    except MapGenerationError as e:
        # WMS errors if no zoom level 19 or 18 is available. In case of this error
        # fallback to zoom level 17 which is available world wide.
        if layer == "esri-world-imagery":
            return get_map_image(
                bbox,
                size,
                "esri-world-imagery-fallback",
            )
        else:
            raise e
    return image


def get_map(
    bbox: Bbox,
    size: Size,
    layer: str,
    format: Literal["png", "jpeg"],
) -> Response:
    """Request a map from the WMS."""
    url = getattr(CONFIG, f"wms_url_{layer.replace('-', '_')}")
    layers = getattr(CONFIG, f"wms_layers_{layer.replace('-', '_')}")
    params = {
        "REQUEST": "GetMap",
        "FORMAT": "image/{0}".format(format),
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
            timeout=(10, int(CONFIG.wms_read_timeout)),
        )
    except ReadTimeout:
        raise MapGenerationError(
            N_(
                "Map area couldn't be processed with the current resources."
                " Please try again once."
            )
        )


def as_image(
    response: Response,
    format: Literal["png", "jpeg"],
) -> Image.Image:
    response_content = response.content
    content_type = response.headers["content-type"]
    response.close()
    try:
        return Image.open(BytesIO(response_content), formats=[format])
    except UnidentifiedImageError:
        if content_type == "application/vnd.ogc.se_xml":
            # Response is an XML error report
            raise MapGenerationError(
                N_(
                    "The Web Map Service returned an error. Please try again later."
                    " Response from the WMS:\n{ERROR_MSG}"
                ),
                {"ERROR_MSG": escape(response_content.decode("utf8"))},
            )
        raise MapGenerationError(
            N_("The Web Map Service returned an error. Please try again later.")
        )
