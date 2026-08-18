import numpy as np
import pytest
import torch
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from ultralytics import YOLO
from ultralytics_MB import YOLO as YOLO_MB

from sketch_map_tool.config import CONFIG
from sketch_map_tool.upload_processing.detect_markings import (
    detect_markings,
)
from sketch_map_tool.upload_processing.ml_models import (
    init_model,
    select_computation_device,
)


# Initialize ml-models.
# NOTE: Usually, this happens for each Celery worker (`init_worker_ml_models`).
@pytest.fixture
def sam_predictor():
    """Zero shot segment anything model"""
    device = select_computation_device()
    sam2_model = build_sam2(
        config_file=CONFIG.model_type_sam,
        ckpt_path=None,
        device=device,
    )
    sam2_model.load_state_dict(
        torch.load(init_model(CONFIG.sam_checkpoint), map_location=device)
    )
    return SAM2ImagePredictor(sam2_model)


@pytest.fixture
def yolo_osm_obj() -> YOLO_MB:
    """YOLO Object Detection"""
    path = init_model(CONFIG.yolo_osm_obj)
    return YOLO_MB(path)


@pytest.fixture
def yolo_esri_obj() -> YOLO_MB:
    """YOLO Object Detection"""
    path = init_model(CONFIG.yolo_osm_obj)
    return YOLO_MB(path)


@pytest.fixture
def yolo_cls() -> YOLO:
    """YOLO Classification"""
    path = init_model(CONFIG.yolo_cls)
    return YOLO(path)


@pytest.mark.limit_memory("2.0 GB")
def test_detect_markings(
    layer,
    map_frame_marked,
    map_frame,
    yolo_osm_obj,
    yolo_esri_obj,
    yolo_cls,
    sam_predictor,
):
    """Test ML-pipeline with memory limit.

    If this test fails because the memory limit has been exceeded,
    than changes to ML-models lead to an increased memory Consumption.
    In this case resource availability in production need to be validated.
    """
    if layer == "osm":
        yolo_obj = yolo_osm_obj
    else:
        yolo_obj = yolo_esri_obj
    markings = detect_markings(  # noqa
        map_frame_marked,
        np.asarray(Image.open(map_frame)),
        yolo_obj,
        yolo_cls,
        sam_predictor,
    )

    # NOTE: uncomment for manual/visual assessment of detected markings
    # NOTE: this is not an approval tests since the clipping is not deterministic
    # TODO: one marking for esri layer is not detected
    # from PIL import ImageDraw, ImageOps
    #
    # img = Image.fromarray(map_frame_marked)
    # for m in markings:
    #     m[m == m.max()] = 255
    #     colored_marking = ImageOps.colorize(
    #         Image.fromarray(m).convert("L"), black="black", white="green"
    #     )
    #     img.paste(colored_marking, (0, 0), Image.fromarray(m))
    #     # draw bbox around each marking, derived from the mask m
    #     bbox = (
    #         np.min(np.where(m)[1]),
    #         np.min(np.where(m)[0]),
    #         np.max(np.where(m)[1]),
    #         np.max(np.where(m)[0]),
    #     )
    #
    #     draw = ImageDraw.Draw(img)
    #     draw.rectangle(bbox, outline="red", width=2)
    # img.show()
