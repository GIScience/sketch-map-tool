import requests

from sketch_map_tool.models import Bbox

OQT_API_URL = "https://oqt.ohsome.org/api"
OQT_REPORT_NAME = "SketchmapFitness"


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
    url = OQT_API_URL + "/" + "report"
    parameters = {
        "name": OQT_REPORT_NAME,
        "bpolys": bbox_to_polygon(bbox),
        "includeSvg": include_svg,
        "includeHtml": include_html,
        "flatten": False,
    }
    req = requests.post(url, json=parameters)
    report_properties = req.json()["properties"]
    return report_properties
