"""OpenAerialMap STAC API Client

Example request to retrieve an image given a bounding box and size:
https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/59e62beb3d6412ef7220c58e/bbox/39.22999959389618,-6.841535317101005,39.25606520781678,-6.819872968487459/1716x1436.png?assets=visual
"""

import requests

from sketch_map_tool.models import Bbox, Size

BASE_API_URL = "https://api.imagery.hotosm.org"
STAC_API_URL = BASE_API_URL + "/stac"
RAST_API_URL = BASE_API_URL + "/raster"
COLLECTION_ID = "openaerialmap"


def get_metadata(item_id: str) -> dict:
    url = f"{STAC_API_URL}/collections/{COLLECTION_ID}/items/{item_id}"
    response = requests.get(url)
    return response.json()


def get_image(item_id: str, size: Size, bbox_wgs84: Bbox):
    url = f"{RAST_API_URL}/collections/{COLLECTION_ID}/items/{item_id}/bbox/{bbox_wgs84}/{size}.png?assets=visual"  # noqa
    response = requests.get(url)
    return response.content


def get_attribution(item_id) -> str:
    # TODO
    # static getMapAttributionFromMetadata(metadataJson) {
    #     const props = metadataJson.properties;
    #     const provider = props.providers.map(provider=> provider.name).join();
    #     return `© <a href="https://map.openaerialmap.org" target="_blank">OpenAerialMap</a> | ${props.title} by ${provider}`;  # noqa
    # }
    raise NotImplementedError
