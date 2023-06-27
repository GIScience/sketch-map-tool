import requests

from sketch_map_tool.exceptions import OQTReportError
from sketch_map_tool.models import Bbox

OQT_API_URL = "https://oqt.ohsome.org/api"
OQT_REPORT_NAME = "sketchmap-fitness"


def bbox_to_polygon(bbox: Bbox) -> dict:
    polygon = {
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
    return polygon


def get_report(bbox: Bbox, include_svg: bool = True, include_html: bool = False):
    url = OQT_API_URL + "/" + "reports" + "/" + OQT_REPORT_NAME
    parameters = {
        "bpolys": bbox_to_polygon(bbox),
        "includeSvg": include_svg,
        "includeHtml": include_html,
        "flatten": False,
    }
    req = requests.post(url, json=parameters)
    if req.status_code == 422:
        if req.json()["type"] == "SizeRestrictionError":
            raise OQTReportError(
                "Selected Area-of-Interest is too large for a Map Quality Check Report."
            )
        else:
            raise OQTReportError(req.json()["detail"])
    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError:
        raise OQTReportError(
            "There seems to be a problem with OQT. Please try again later."
        )
    report_properties = req.json()["properties"]
    return report_properties
