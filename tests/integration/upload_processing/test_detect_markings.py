import logging

import numpy as np
import pytest
from PIL import Image, ImageEnhance
from segment_anything import SamPredictor, sam_model_registry
from ultralytics import YOLO
from ultralytics_4bands import YOLO as YOLO_4

from sketch_map_tool.config import get_config_value
from sketch_map_tool.upload_processing.detect_markings import (
    detect_markings,
)
from sketch_map_tool.upload_processing.ml_models import init_model


# Initialize ml-models.
# This usually happens inside the celery task: `digitize_sketches`
@pytest.fixture
def sam_predictor():
    """Zero shot segment anything model"""
    sam_path = init_model(get_config_value("neptune_model_id_sam"))
    sam_model = sam_model_registry[get_config_value("model_type_sam")](sam_path)
    return SamPredictor(sam_model)  # mask predictor


@pytest.fixture
def yolo_osm_obj() -> YOLO_4:
    """YOLO Object Detection"""
    path = init_model(get_config_value("neptune_model_id_yolo_osm_obj"))
    return YOLO_4(path)


@pytest.fixture
def yolo_osm_cls() -> YOLO:
    """YOLO Classification"""
    path = init_model(get_config_value("neptune_model_id_yolo_osm_cls"))
    return YOLO(path)


@pytest.fixture
def yolo_esri_obj() -> YOLO_4:
    """YOLO Object Detection"""
    path = init_model(get_config_value("neptune_model_id_yolo_osm_obj"))
    return YOLO_4(path)


@pytest.fixture
def yolo_esri_cls() -> YOLO:
    """YOLO Classification"""
    path = init_model(get_config_value("neptune_model_id_yolo_osm_cls"))
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
    for m in markings:
        img = Image.fromarray(m)
        ImageEnhance.Contrast(img).enhance(10).show()


def test_detectec_markings_failure(yolo_osm_cls, yolo_osm_obj, sam_predictor, caplog):
    # Empty map and template should not contain any markings
    empty_map = np.zeros((1024, 1024, 3), dtype=np.uint8)
    empty_template = np.zeros((1024, 1024, 3), dtype=np.uint8)

    with caplog.at_level(logging.WARNING):
        detect_markings(
            empty_map,
            empty_template,
            yolo_osm_obj,
            yolo_osm_cls,
            sam_predictor,
        )
        assert "No markings detected." in caplog.text
