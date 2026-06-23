import os
from datetime import datetime
from io import BytesIO

import pytest
from pytest_approval import verify_image

from sketch_map_tool import usage_charts

pytestmark = [
    pytest.mark.skipif(
        os.environ.get("CI") is not None,
        reason="Fonts are different in CI and triggers a failure of approval tests.",
    )
]

data = [
    {
        "uuid": "5a47f9eb-7c32-46b5-8e64-a15eec6ebae2",
        "bbox": "POLYGON ((967434.6098457306 6343459.035638228, 967434.6098457306 6345977.635778541, 964472.1973848869 6345977.635778541, 964472.1973848869 6343459.035638228, 967434.6098457306 6343459.035638228))",  # noqa
        "bbox_wgs84": "POLYGON ((8.7334 49.3711, 8.7334 49.4397, 8.625 49.4397, 8.625 49.3711, 8.7334 49.3711))",  # noqa
        "centroid": "POINT (965953.4036153088 6344718.3357083835)",
        "centroid_wgs84": "POINT (8.6792 49.40539999999999)",
        "format": "a4",
        "orientation": "landscape",
        "layer": "osm",
        "created": datetime(2026, 6, 11),
        "downloaded": datetime(2026, 6, 11),
        "iso_a2": "de",
        "uploads": 1,
        "downloads": 0,
        "downloads_raster": 0,
        "downloads_vector": 0,
        "consenses": 1,
    },
    {
        "uuid": "a1a08111-4a74-45b9-bfe5-3099b43a067f",
        "bbox": "POLYGON ((967434.6098457306 6343459.035638228, 967434.6098457306 6345977.635778541, 964472.1973848869 6345977.635778541, 964472.1973848869 6343459.035638228, 967434.6098457306 6343459.035638228))",  # noqa
        "bbox_wgs84": "POLYGON ((8.7334 49.3711, 8.7334 49.4397, 8.625 49.4397, 8.625 49.3711, 8.7334 49.3711))",  # noqa
        "centroid": "POINT (965953.4036153088 6344718.3357083835)",
        "centroid_wgs84": "POINT (8.6792 49.40539999999999)",
        "format": "a4",
        "orientation": "landscape",
        "layer": "esri-world-imagery",
        "created": datetime(2026, 6, 11),
        "downloaded": None,
        "iso_a2": "us",
        "uploads": 0,
        "downloads": 0,
        "downloads_raster": 0,
        "downloads_vector": 0,
        "consenses": 1,
    },
    {
        "uuid": "2f6b20f4-dade-4c8e-a783-7068e0951836",
        "bbox": "POLYGON ((967434.6098457306 6343459.035638228, 967434.6098457306 6345977.635778541, 964472.1973848869 6345977.635778541, 964472.1973848869 6343459.035638228, 967434.6098457306 6343459.035638228))",  # noqa
        "bbox_wgs84": "POLYGON ((39.25606520781678 -6.841535317101005, 39.25606520781678 -6.819872968487459, 39.22999959389618 -6.819872968487459, 39.22999959389618 -6.841535317101005, 39.25606520781678 -6.841535317101005))",  # noqa
        "centroid": "POINT (965953.4036153088 6344718.3357083835)",
        "centroid_wgs84": "POINT (39.243032400856485 -6.830704142794232)",
        "format": "a4",
        "orientation": "landscape",
        "layer": "oam:59e62beb3d6412ef7220c58e",
        "created": datetime(2026, 8, 11),
        "downloaded": datetime(2026, 8, 11),
        "iso_a2": None,
        "uploads": 5,
        "downloads": 1,
        "downloads_raster": 0,
        "downloads_vector": 1,
        "consenses": 1,
    },
]


def test_created_and_downloaded_sketch_maps():
    chart = usage_charts.get_created_sketch_maps(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")


def test_uploads_and_downloads():
    chart = usage_charts.get_detected_markings(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")


def test_layer_distribution():
    chart = usage_charts.layer_distribution(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")


def test_format_distribution():
    chart = usage_charts.format_distribution(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")


def test_result_download_distribution():
    chart = usage_charts.result_download_distribution(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")


def test_consent_distribution():
    chart = usage_charts.consent_distribution(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")


def test_sketch_maps_by_country_map():
    chart = usage_charts.sketch_maps_by_country_map(data)
    buffer = BytesIO()
    chart.render_to_png(buffer)
    assert verify_image(buffer.getvalue(), extension=".png")
