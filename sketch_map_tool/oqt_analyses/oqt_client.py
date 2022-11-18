from typing import List

import requests

OQT_API_URL = "https://oqt.ohsome.org/api"
OQT_REPORT_NAME = "SketchmapFitness"


def bbox_to_polygon(bbox: List[float]) -> dict:
    if len(bbox) != 4:
        raise ValueError("Bbox doesn't have 4 floating values.")
    polygon = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]
            ],
        },
    }
    return polygon


def get_report(bbox: List[float]):
    url = OQT_API_URL + "/" + "report"
    parameters = {
        "name": OQT_REPORT_NAME,
        "bpolys": bbox_to_polygon(bbox),
        "includeSvg": False,
        "includeHtml": True,
        "flatten": False,
    }
    req = requests.post(url, json=parameters)
    html = req.json()["properties"]["report"]["result"]["html"]
    return html
