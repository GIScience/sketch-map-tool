from types import MappingProxyType

import cv2
import numpy as np
import pytest

from sketch_map_tool.upload_processing.marking_detection import detect_markings
from tests import FIXTURE_DIR

MARKING_DETECTION_FIXTURE_DIR = FIXTURE_DIR / "marking-detection"


@pytest.fixture
def basemap_marking_img_screenshot():
    return cv2.imread(
        str(MARKING_DETECTION_FIXTURE_DIR / "screenshot-base-map.jpg")
    ), cv2.imread(str(MARKING_DETECTION_FIXTURE_DIR / "screenshot-markings.jpg"))


@pytest.fixture
def basemap_marking_img_photo():
    return cv2.imread(
        str(MARKING_DETECTION_FIXTURE_DIR / "photo-base-map.jpg")
    ), cv2.imread(str(MARKING_DETECTION_FIXTURE_DIR / "photo-markings.jpg"))


@pytest.fixture
def basemap_marking_img_scan():
    return cv2.imread(
        str(MARKING_DETECTION_FIXTURE_DIR / "scan-base-map.jpg")
    ), cv2.imread(str(MARKING_DETECTION_FIXTURE_DIR / "scan-markings.jpg"))


def test_marking_detection_screenshot(basemap_marking_img_screenshot):
    base_map, markings = basemap_marking_img_screenshot
    detected_markings = detect_markings(base_map, markings)
    for colour, img in detected_markings:
        assert isinstance(colour, str)
        assert isinstance(img, np.ndarray)


def test_marking_detection_photo(basemap_marking_img_photo):
    base_map, markings = basemap_marking_img_photo
    detected_markings = detect_markings(base_map, markings)
    for colour, img in detected_markings:
        assert isinstance(colour, str)
        assert isinstance(img, np.ndarray)


def test_marking_detection_scan(basemap_marking_img_scan):
    base_map, markings = basemap_marking_img_scan
    detected_markings = detect_markings(base_map, markings)
    for colour, img in detected_markings:
        assert isinstance(colour, str)
        assert isinstance(img, np.ndarray)
