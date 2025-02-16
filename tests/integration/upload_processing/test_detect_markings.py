import random

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageOps
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from ultralytics import YOLO
from ultralytics_MB import YOLO as YOLO_MB

from sketch_map_tool.config import get_config_value
from sketch_map_tool.upload_processing.detect_markings import (
    detect_markings,
)
from sketch_map_tool.upload_processing.ml_models import (
    init_model,
    init_sam2,
    select_computation_device,
)


# Initialize ml-models.
# This usually happens inside the celery task: `digitize_sketches`
@pytest.fixture
def sam_predictor():
    """Zero shot segment anything model"""
    path = init_sam2()
    device = select_computation_device()
    sam2_model = build_sam2(
        config_file="sam2_hiera_b+.yaml",
        ckpt_path=path,
        device=device,
    )
    return SAM2ImagePredictor(sam2_model)


@pytest.fixture
def yolo_osm_obj() -> YOLO_MB:
    """YOLO Object Detection"""
    path = init_model(get_config_value("yolo_osm_obj"))
    return YOLO_MB(path)


@pytest.fixture
def yolo_osm_cls() -> YOLO:
    """YOLO Classification"""
    path = init_model(get_config_value("yolo_osm_cls"))
    return YOLO(path)


@pytest.fixture
def yolo_esri_obj() -> YOLO_MB:
    """YOLO Object Detection"""
    path = init_model(get_config_value("yolo_osm_obj"))
    return YOLO_MB(path)


@pytest.fixture
def yolo_esri_cls() -> YOLO:
    """YOLO Classification"""
    path = init_model(get_config_value("yolo_osm_cls"))
    return YOLO(path)


@pytest.mark.skip("For manuel testing")
def test_detect_markings(
    layer,
    map_frame_marked,
    map_frame,
    yolo_osm_obj,
    yolo_osm_cls,
    yolo_esri_obj,
    yolo_esri_cls,
    sam_predictor,
):
    if layer.value == "osm":
        yolo_obj = yolo_osm_obj
        yolo_cls = yolo_osm_cls
    else:
        yolo_obj = yolo_esri_obj
        yolo_cls = yolo_esri_cls
    markings = detect_markings(
        map_frame_marked,
        np.asarray(Image.open(map_frame)),
        yolo_obj,
        yolo_cls,
        sam_predictor,
    )

    img = Image.fromarray(map_frame_marked)
    for m in markings:
        colors = ["red", "green", "blue", "yellow", "purple", "orange", "pink", "brown"]
        m[m == m.max()] = 255
        colored_marking = ImageOps.colorize(
            Image.fromarray(m).convert("L"), black="black", white=random.choice(colors)
        )
        img.paste(colored_marking, (0, 0), Image.fromarray(m))
        # draw bbox around each marking, derived from the mask m
        bbox = (
            np.min(np.where(m)[1]),
            np.min(np.where(m)[0]),
            np.max(np.where(m)[1]),
            np.max(np.where(m)[0]),
        )

        draw = ImageDraw.Draw(img)
        draw.rectangle(bbox, outline="red", width=2)

    img.show()
