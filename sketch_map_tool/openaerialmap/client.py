"""OpenAerialMap STAC API Client

Example request to retrieve an image given a bounding box and size:
https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/59e62beb3d6412ef7220c58e/bbox/39.22999959389618,-6.841535317101005,39.25606520781678,-6.819872968487459/1716x1436.png?assets=visual
"""

import logging
from io import BytesIO

import requests
from PIL import Image

from sketch_map_tool.exceptions import MapGenerationError
from sketch_map_tool.helpers import N_
from sketch_map_tool.models import Bbox, Size

BASE_API_URL = "https://api.imagery.hotosm.org"
STAC_API_URL = BASE_API_URL + "/stac"
RAST_API_URL = BASE_API_URL + "/raster"
COLLECTION_ID = "openaerialmap"


def get_metadata(item_id: str) -> dict:
    item_id = item_id.replace("oam:", "")
    url = f"{STAC_API_URL}/collections/{COLLECTION_ID}/items/{item_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_map_image(bbox_wgs84: Bbox, size: Size, item_id: str) -> Image.Image:
    item_id = item_id.replace("oam:", "")
    url = f"{RAST_API_URL}/collections/{COLLECTION_ID}/items/{item_id}/bbox/{bbox_wgs84}/{size}.png?assets=visual"  # noqa
    response = requests.get(url)
    if response.status_code == 404:
        logging.error("Could not find OpenAerialMap item for url: " + url)
        raise MapGenerationError(N_("Could not find OpenAerialMap item."))
    response.raise_for_status()
    return Image.open(BytesIO(response.content), formats=["png"])


def get_attribution(item_id) -> str:
    metadata = get_metadata(item_id)
    providers = ", ".join([p["name"] for p in metadata["properties"]["providers"]])
    return f"Powered by OpenAerialMap<br />Providers: {providers}"
