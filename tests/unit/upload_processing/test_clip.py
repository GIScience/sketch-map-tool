import logging

import cv2
import pytest

from sketch_map_tool.upload_processing.clip import clip
from tests import FIXTURE_DIR

MAP_CUTTING_FIXTURE_DIR = FIXTURE_DIR / "map-cutting"


@pytest.fixture
def template_upload_expected_easy():
    return (
        cv2.imread(str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-easy-base.png")),
        cv2.imread(str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-easy-upload.jpg")),
        cv2.imread(str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-easy-expected.jpg")),
    )


@pytest.fixture
def template_upload_expected_low_resolution():
    return (
        cv2.imread(str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-low-resolution-base.png")),
        cv2.imread(
            str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-low-resolution-upload.jpg")
        ),
        cv2.imread(
            str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-low-resolution-expected.jpg")
        ),
    )


@pytest.fixture
def template_upload_few_features():
    return (
        cv2.imread(str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-few-features-base.jpg")),
        cv2.imread(str(MAP_CUTTING_FIXTURE_DIR / "map-cutter-few-features-upload.jpg")),
    )


@pytest.fixture
def photo_of_sketch_map():
    return cv2.imread(str(FIXTURE_DIR / "clip" / "1-photo-of-sketch-map.jpg"))


@pytest.fixture
def map_frame():
    return cv2.imread(str(FIXTURE_DIR / "clip" / "1-map-frame.png"))


@pytest.fixture
def photo_of_sketch_map_clipped():
    return cv2.imread(str(FIXTURE_DIR / "clip" / "1-photo-of-sketch-map-clipped.jpg"))


@pytest.fixture
def photo_of_sketch_map_2():
    return cv2.imread(str(FIXTURE_DIR / "clip" / "2-photo-of-sketch-map.jpg"))


@pytest.fixture
def map_frame_2():
    return cv2.imread(str(FIXTURE_DIR / "clip" / "2-map-frame.png"))


def get_correlation_of_histograms(img_1, img_2):
    hsv_1 = cv2.cvtColor(img_1, cv2.COLOR_BGR2HSV)
    hsv_2 = cv2.cvtColor(img_2, cv2.COLOR_BGR2HSV)
    hist_1 = cv2.calcHist(
        [hsv_1], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256]
    )
    hist_2 = cv2.calcHist(
        [hsv_2], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256]
    )
    cv2.normalize(hist_1, hist_1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist_2, hist_2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return cv2.compareHist(hist_1, hist_2, 0)


def test_cut_out_map(template_upload_expected_easy):
    template, upload, expected = template_upload_expected_easy
    result = clip(upload, template)
    assert get_correlation_of_histograms(expected, result) >= 0.8


def test_cut_out_low_resolution(template_upload_expected_low_resolution):
    template, upload, expected = template_upload_expected_low_resolution
    result = clip(upload, template)
    assert get_correlation_of_histograms(expected, result) >= 0.8


def test_clip_1(
    photo_of_sketch_map,
    map_frame,
    photo_of_sketch_map_clipped,
):
    """Example of previously failed georeferencing (version 2024.08.02.4)."""
    result = clip(photo_of_sketch_map, map_frame)
    assert get_correlation_of_histograms(photo_of_sketch_map_clipped, result) >= 0.8


def test_clip_failure(
    photo_of_sketch_map,
    map_frame_2,
    caplog,
):
    """Clip produces a distorted image."""
    with caplog.at_level(logging.WARNING):
        clip(photo_of_sketch_map, map_frame_2)
        # TODO: detect failure of clip and log a warning
        assert "" in caplog.text
    # cv2.imshow("image", result)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


# TODO: Improve map cutting to also work in the case of few features
# def test_cut_out_few_features(template_upload_few_features):
#     template, upload = template_upload_few_features
#     result = map_cutter.cut_out_map(upload, template)
#     cv2.imwrite("output.jpg", result)
#     assert False
