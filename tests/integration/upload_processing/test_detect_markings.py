import matplotlib.pyplot as plt
import pytest
from numpy import asarray
from PIL import Image, ImageEnhance
from segment_anything import SamPredictor, sam_model_registry
from ultralytics import YOLO

from sketch_map_tool.config import get_config_value
from sketch_map_tool.upload_processing.detect_markings import (
    apply_ml_pipeline,
    detect_markings,
)
from sketch_map_tool.upload_processing.ml_models import init_model


# Initialize ml-models.
# This usually happens inside the celery task: `digitize_sketches`
@pytest.fixture
def sam_predictor():
    # Zero shot segment anything model
    sam_path = init_model(get_config_value("neptune_model_id_sam"))
    sam_model = sam_model_registry["vit_b"](sam_path)
    return SamPredictor(sam_model)  # mask predictor


@pytest.fixture
def yolo_model():
    # Custom trained model for object detection of markings and colors
    yolo_path = init_model(get_config_value("neptune_model_id_yolo"))
    return YOLO(yolo_path)


@pytest.mark.skip("For manuel testing")
def test_detect_markings(sam_predictor, yolo_model, map_frame_markings_buffer):
    img = asarray(Image.open(map_frame_markings_buffer))
    markings = detect_markings(img, yolo_model, sam_predictor)
    img = Image.fromarray(markings)
    ImageEnhance.Contrast(img).enhance(10).show()
    breakpoint()


def test_apply_ml_pipeline(sam_predictor, yolo_model, map_frame_markings_buffer):
    img = Image.open(map_frame_markings_buffer).convert("RGB")
    masks, colors = apply_ml_pipeline(img, yolo_model, sam_predictor)
    # TODO: Should the len not be 2? Only two markings are on the input image.
    assert len(masks) == len(colors) == 6


@pytest.mark.skip("For manuel testing")
def test_apply_ml_pipeline_show_masks(
    sam_predictor, yolo_model, map_frame_markings_buffer
):
    img = Image.open(map_frame_markings_buffer).convert("RGB")
    masks, _ = apply_ml_pipeline(img, yolo_model, sam_predictor)
    for mask in masks:
        plt.imshow(mask, cmap="viridis", alpha=0.7)
        plt.show()
