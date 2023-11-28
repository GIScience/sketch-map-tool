# -*- coding: utf-8 -*-
"""
Functions to process images of sketch maps and detect markings on them
"""

import numpy as np
from PIL import Image
from numpy.typing import NDArray
from segment_anything import SamPredictor
from ultralytics import YOLO


def create_marking_array(
        masks: list[NDArray],
        colors: list[str],
        sketch_map_frame: NDArray,
) -> NDArray:
    """
    Create a single color marking array based on masks and colors.

    Parameters:
    - masks (list[NDArray]): List of masks representing markings.
    - colors (list[str]): List of colors corresponding to each mask.
    - sketch_map_frame (NDArray): Original sketch map frame.

    Returns:
    NDArray: Single color marking array.
    """
    single_color_marking = np.zeros((sketch_map_frame.shape[0], sketch_map_frame.shape[1]), dtype=np.uint8)
    for color, mask in zip(colors, masks):
        single_color_marking[mask] = color
    return single_color_marking


def apply_yolo(image: Image, yolo_model: YOLO):
    """
    Apply YOLO object detection on an image.

    Parameters:
    - image (Image): Input image.
    - yolo_model (YOLO): YOLO model.

    Returns:
    tuple: Detected bounding boxes and corresponding class labels.
    """
    result = yolo_model(image)[0].boxes
    bounding_boxes = result.xyxy
    class_labels = result.cls
    return bounding_boxes, class_labels


def mask_from_bbox(bbox, mask_predictor: SamPredictor):
    """
    Generate a mask using SAM (Segment Anything) predictor for a given bounding box.

    Parameters:
    - bbox: Bounding box coordinates.
    - mask_predictor (SamPredictor): SAM predictor model.

    Returns:
    tuple: Mask and corresponding score.
    """
    masks, scores, logits = mask_predictor.predict(
        box=bbox,
        multimask_output=False
    )
    return masks[0], scores[0]


def apply_sam(image: Image, bounding_boxes: list, mask_predictor: SamPredictor):
    """
    Apply SAM (Segment Anything) on an image using bounding boxes.

    Parameters:
    - image (Image): Input image.
    - bounding_boxes (list): List of bounding boxes.
    - mask_predictor (SamPredictor): SAM predictor model.

    Returns:
    tuple: List of masks and corresponding scores.
    """
    mask_predictor.set_image(np.array(image))
    masks = []
    scores = []
    for i, bbox in enumerate(bounding_boxes):
        mask, score = mask_from_bbox(np.array(bbox), mask_predictor)
        masks.append(mask)
        scores.append(score)
    return masks, scores


def apply_ml_pipeline(image: Image, yolo_model: YOLO, mask_predictor: SamPredictor):
    """
    Apply the entire machine learning pipeline on an image.

    Parameters:
    - image (Image): Input image.
    - yolo_model (YOLO): YOLO object detection model.
    - mask_predictor (SamPredictor): SAM predictor model.

    Returns:
    tuple: List of masks and class labels.
    """
    bounding_boxes, class_labels = apply_yolo(image, yolo_model)
    masks, scores = apply_sam(image, bounding_boxes, mask_predictor)
    return masks, class_labels
