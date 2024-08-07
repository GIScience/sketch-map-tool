import requests

from sketch_map_tool.exceptions import OQTReportError
from sketch_map_tool.helpers import N_
from sketch_map_tool.models import Bbox

OQT_API_URL = "https://api.quality.ohsome.org/v1"
OQT_REPORT_NAME = "sketchmap-fitness"


def bbox_to_feature_collection(bbox: Bbox) -> dict:
    polygon = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [bbox.lon_min, bbox.lat_min],
                            [bbox.lon_max, bbox.lat_min],
                            [bbox.lon_max, bbox.lat_max],
                            [bbox.lon_min, bbox.lat_max],
                            [bbox.lon_min, bbox.lat_min],
                        ]
                    ],
                },
            }
        ],
    }
    return polygon


def get_report(bbox: Bbox):
    url = OQT_API_URL + "/" + "reports" + "/" + OQT_REPORT_NAME
    parameters = {"bpolys": bbox_to_feature_collection(bbox)}
    req = requests.post(
        url,
        json=parameters,
        timeout=(10, 600),  # connect timeout (5 seconds), read_timeout (10 minutes)
    )
    if req.status_code == 422:
        if req.json()["type"] == "SizeRestrictionError":
            raise OQTReportError(
                N_(
                    "Selected Area-of-Interest is too large "
                    "for a Map Quality Check Report."
                )
            )
        else:
            raise OQTReportError(req.json()["detail"])
    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError:
        raise OQTReportError(
            N_("There seems to be a problem with OQT. Please try again later.")
        )
    return req.json()["features"][0]["properties"]
