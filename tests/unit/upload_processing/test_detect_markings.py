import cv2
import numpy as np
import pytest

from sketch_map_tool.definitions import COLORS
from sketch_map_tool.upload_processing.detect_markings import detect_markings
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
    for color in COLORS:
        detected_markings = detect_markings(base_map, markings, color)
        assert isinstance(detected_markings, np.ndarray)


def test_marking_detection_map_frame(map_frame, map_frame_markings):
    for color in COLORS:
        detected_markings = detect_markings(map_frame, map_frame_markings, color)
        assert isinstance(detected_markings, np.ndarray)
        # Too manually check the image uncomment following code.
        # cv2.imshow("image", img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


def test_marking_detection_photo(basemap_marking_img_photo):
    base_map, markings = basemap_marking_img_photo
    for color in COLORS:
        detected_markings = detect_markings(base_map, markings, color)
        assert isinstance(detected_markings, np.ndarray)


def test_marking_detection_scan(basemap_marking_img_scan):
    base_map, markings = basemap_marking_img_scan
    for color in COLORS:
        detected_markings = detect_markings(base_map, markings, color)
        assert isinstance(detected_markings, np.ndarray)
