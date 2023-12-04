import pytest
from PIL import Image

from sketch_map_tool.upload_processing.create_marking_array import (
    apply_ml_pipeline,
    applySAM,
    applyYOLO,
    mask_predictor,
    modelYOLO,
)
from tests import FIXTURE_DIR

MARKING_DETECTION_FIXTURE_DIR = FIXTURE_DIR / "marking-detection"


@pytest.fixture
def basemap_marking_img_screenshot():
    return Image.open(
        str(MARKING_DETECTION_FIXTURE_DIR / "screenshot-base-map.jpg")
    ), Image.open(str(MARKING_DETECTION_FIXTURE_DIR / "screenshot-markings.jpg"))


@pytest.fixture
def basemap_marking_img_photo():
    return Image.open(
        str(MARKING_DETECTION_FIXTURE_DIR / "photo-base-map.jpg")
    ), Image.open(str(MARKING_DETECTION_FIXTURE_DIR / "photo-markings.jpg"))


@pytest.fixture
def basemap_marking_img_scan():
    return Image.open(
        str(MARKING_DETECTION_FIXTURE_DIR / "scan-base-map.jpg")
    ), Image.open(str(MARKING_DETECTION_FIXTURE_DIR / "scan-markings.jpg"))


def test_yolo_detection_screenshot(basemap_marking_img_screenshot):
    base_map, markings = basemap_marking_img_screenshot
    bboxes, colors = applyYOLO(markings, modelYOLO)
    assert len(bboxes) == 13
    assert len(colors) == 13
    assert len(colors) == len(bboxes)


def test_yolo_detection_photo(basemap_marking_img_photo):
    base_map, markings = basemap_marking_img_photo
    bboxes, colors = applyYOLO(markings, modelYOLO)
    print(len(bboxes))
    assert len(bboxes) == 13
    assert len(colors) == 13
    assert len(colors) == len(bboxes)


def test_yolo_detection_scan(basemap_marking_img_scan):
    base_map, markings = basemap_marking_img_scan
    bboxes, colors = applyYOLO(markings, modelYOLO)
    print(len(bboxes))
    assert len(bboxes) == 14
    assert len(colors) == 14
    assert len(colors) == len(bboxes)


def test_sam_mask_generation_screenshot(basemap_marking_img_screenshot):
    base_map, markings = basemap_marking_img_screenshot
    markings = markings.convert("RGB")
    bboxes, colors = applyYOLO(markings, modelYOLO)
    masks, scores = applySAM(markings, bboxes, mask_predictor)
    assert len(masks) == len(bboxes)


def test_sam_mask_generation_photo(basemap_marking_img_photo):
    base_map, markings = basemap_marking_img_photo
    markings = markings.convert("RGB")
    bboxes, colors = applyYOLO(markings, modelYOLO)
    masks, scores = applySAM(markings, bboxes, mask_predictor)
    assert len(masks) == len(bboxes)


def test_sam_mask_generation_scan(basemap_marking_img_scan):
    base_map, markings = basemap_marking_img_scan
    markings = markings.convert("RGB")
    bboxes, colors = applyYOLO(markings, modelYOLO)
    masks, scores = applySAM(markings, bboxes, mask_predictor)
    assert len(masks) == len(bboxes)


def test_applyPipeline_screenshot(basemap_marking_img_screenshot):
    base_map, markings = basemap_marking_img_screenshot
    markings = markings.convert("RGB")
    masks, colors = apply_ml_pipeline(markings)
    assert len(masks) == len(colors)
    assert len(masks) == 13


def test_applyPipeline_photo(basemap_marking_img_photo):
    base_map, markings = basemap_marking_img_photo
    markings = markings.convert("RGB")
    masks, colors = apply_ml_pipeline(markings)
    assert len(masks) == len(colors)
    assert len(masks) == 13


def test_applyPipeline_scan(basemap_marking_img_scan):
    base_map, markings = basemap_marking_img_scan
    markings = markings.convert("RGB")
    masks, colors = apply_ml_pipeline(markings)
    assert len(masks) == len(colors)
    assert len(masks) == 14
