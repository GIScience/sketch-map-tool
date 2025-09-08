import json
import logging
import os
from pathlib import Path
from typing import Literal

import requests
from werkzeug.utils import secure_filename

from sketch_map_tool.config import get_config_value
from sketch_map_tool.models import Layer, LiteratureReference, PaperFormat

# Types of requests
REQUEST_TYPES = Literal["sketch-map", "raster-results", "vector-results"]
# Colors to be detected
COLORS = {
    "1": "black",
    "2": "blue",
    "3": "green",
    "4": "orange",
    "5": "pink",
    "6": "red",
    "7": "yellow",
}
# Resources for PDF generation
PDF_RESOURCES_PATH = Path(__file__).parent.resolve() / "resources"


def get_attribution(layer: Layer) -> str:
    """Get attribution text for ESRI World Imagery layer."""
    if layer.value in ("esri-world-imagery", "esri-world-imagery-fallback"):
        url = (
            "https://basemaps-api.arcgis.com/arcgis/rest/services/styles/ArcGIS:Imagery"
        )
        token = get_config_value("esri-api-key")
        if token == "":
            sources = "Esri, Maxar, Earthstar Geographics, and the GIS User Community"
            logging.warning(
                "No ESRI API key configured. "
                + " To retrieve up-to-date attribution from ESRI please add one."
            )
        else:
            params = {"type": "style", "token": token}
            response = requests.get(url, params, timeout=10)
            result = response.json()
            result["sources"].pop("esri", None)
            sources = list(result["sources"].values())[0]["attribution"]
            if len(sources) != 2:
                logging.warning(
                    "Attribution retrieved from ESRI API has unexpected format."
                )
        return "Powered by Esri<br />" + sources
    else:
        return "Powered by OpenStreetMap<br />©openstreetmap.org/copyright"


def get_literature_references() -> list[LiteratureReference]:
    """Read a list of literature references from JSON stored on disk.

    For image source either a web URL or a filename of a file in the publications folder
    is expected.
    """
    p = Path(get_config_value("data-dir")) / "literature.json"
    with open(p, "r") as f:
        raw = json.load(f)

    def create_literature_reference(element) -> LiteratureReference:
        # if image is stored on disk
        img_src = element.get("imgSrc", None)
        if img_src is not None and not img_src.strip().startswith("http"):
            img_src = os.path.join(
                "/static",
                "assets",
                "images",
                "about",
                "publications",
                secure_filename(img_src),
            )
        return LiteratureReference(
            element["citation"],
            img_src,
            element.get("url", None),
        )

    return [create_literature_reference(element) for element in raw]


LITERATURE_REFERENCES = get_literature_references()


A0 = PaperFormat(
    "a0",
    width=118.9,
    height=84.1,
    right_margin=15,
    map_margin=1.0,
    font_size=25,
    qr_scale=1.8,
    compass_scale=1,
    marker_scale=0.5,
    scale_height=36,
    scale_relative_xy=(-15, -90),
    scale_background_params=(-15, -90, 30, 180),
    scale_distance_to_text=50,
    qr_y=1.0,
    indent=0.5,
    qr_contents_distances_not_rotated=(10, 10),
    qr_contents_distance_rotated=10,
)
A1 = PaperFormat(
    "a1",
    width=84.1,
    height=59.4,
    right_margin=12,
    map_margin=1.0,
    font_size=20,
    qr_scale=1.4,
    compass_scale=0.75,
    marker_scale=0.375,
    scale_height=24,
    scale_relative_xy=(-15, -60),
    scale_background_params=(-15, -60, 30, 120),
    scale_distance_to_text=40,
    qr_y=1.0,
    indent=0.5,
    qr_contents_distances_not_rotated=(5, 8),
    qr_contents_distance_rotated=7,
)
A2 = PaperFormat(
    "a2",
    width=59.4,
    height=42,
    right_margin=7.5,
    map_margin=1.0,
    font_size=12,
    qr_scale=0.85,
    compass_scale=0.5,
    marker_scale=0.25,
    scale_height=12,
    scale_relative_xy=(-15, -30),
    scale_background_params=(-15, -30, 30, 60),
    scale_distance_to_text=25,
    qr_y=1.0,
    indent=0.5,
    qr_contents_distances_not_rotated=(6, 4),
    qr_contents_distance_rotated=4,
)
A3 = PaperFormat(
    "a3",
    width=42,
    height=29.7,
    right_margin=7,
    map_margin=1.0,
    font_size=11,
    qr_scale=0.80,
    compass_scale=0.33,
    marker_scale=0.165,
    scale_height=12,
    scale_relative_xy=(-15, -30),
    scale_background_params=(-15, -30, 30, 60),
    scale_distance_to_text=20,
    qr_y=1.0,
    indent=0.5,
    qr_contents_distances_not_rotated=(3, 4),
    qr_contents_distance_rotated=4,
)
A4 = PaperFormat(
    "a4",
    width=29.7,
    height=21,
    right_margin=5,
    map_margin=1.0,
    font_size=8,
    qr_scale=0.6,
    compass_scale=0.25,
    marker_scale=0.125,
    scale_height=12,
    scale_relative_xy=(-15, -30),
    scale_background_params=(-15, -30, 30, 60),
    scale_distance_to_text=20,
    qr_y=1.0,
    indent=0.25,
    qr_contents_distances_not_rotated=(2, 3),
    qr_contents_distance_rotated=3,
)
TABLOID = PaperFormat(
    "tabloid",
    width=43.2,
    height=27.9,
    right_margin=7,
    map_margin=1.0,
    font_size=11,
    qr_scale=0.75,
    compass_scale=0.33,
    marker_scale=0.165,
    scale_height=12,
    scale_relative_xy=(-15, -30),
    scale_background_params=(-15, -30, 30, 60),
    scale_distance_to_text=20,
    qr_y=1.0,
    indent=0.5,
    qr_contents_distances_not_rotated=(3, 4),
    qr_contents_distance_rotated=4,
)
LETTER = PaperFormat(
    "letter",
    width=27.9,
    height=21.6,
    right_margin=5,
    map_margin=1.0,
    font_size=8,
    qr_scale=0.55,
    compass_scale=0.25,
    marker_scale=0.125,
    scale_height=12,
    scale_relative_xy=(-15, -30),
    scale_background_params=(-15, -30, 30, 60),
    scale_distance_to_text=20,
    qr_y=1.0,
    indent=0.25,
    qr_contents_distances_not_rotated=(2, 3),
    qr_contents_distance_rotated=3,
)

ALL_PAPER_FORMATS = [A0, A1, A2, A3, A4, TABLOID, LETTER]

LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
    "cs": "Český",
}
