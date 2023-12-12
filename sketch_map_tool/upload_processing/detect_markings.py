# -*- coding: utf-8 -*-

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from segment_anything import SamPredictor
from ultralytics import YOLO


def detect_markings(
    image: NDArray,
    yolo_model: YOLO,
    sam_predictor: SamPredictor,
) -> NDArray:
    # Sam can only deal with RGB and not RGBA etc.
    img = Image.fromarray(image[:, :, ::-1]).convert("RGB")
    # masks represent markings
    masks, colors = apply_ml_pipeline(img, yolo_model, sam_predictor)
    colors = [int(c) + 1 for c in colors]  # +1 because 0 is background
    return create_marking_array(masks, colors, image)


def apply_ml_pipeline(
    image: Image.Image,
    yolo_model: YOLO,
    sam_predictor: SamPredictor,
) -> tuple[list, list]:
    """Apply the entire machine learning pipeline on an image.

    Steps:
        1. Apply YOLO to detect bounding boxes and label (colors) of objects (markings)
        2. Apply SAM to create binary masks of detected objects

    Returns:
        tuple: A list of masks and class labels.
            Masks are binary numpy arrays with same dimensions as input image
            (map frame), masking the dominant segment inside of a bbox detected by YOLO.
            Class labels are colors.
    """
    bounding_boxes, class_labels = apply_yolo(image, yolo_model)
    masks, _ = apply_sam(image, bounding_boxes, sam_predictor)
    return masks, class_labels


def apply_yolo(
    image: Image.Image,
    yolo_model: YOLO,
) -> tuple[list, list]:
    """Apply fine-tuned YOLO object detection on an image.

    Returns:
        tuple: Detected bounding boxes around individual markings and corresponding
        class labels (colors).
    """
    result = yolo_model(image, conf=0.7)[0].boxes  # TODO set conf parameter
    bounding_boxes = result.xyxy
    class_labels = result.cls
    return bounding_boxes, class_labels


def apply_sam(
    image: Image.Image,
    bounding_boxes: list,
    sam_predictor: SamPredictor,
) -> tuple:
    """Apply zero-shot SAM (Segment Anything) on an image using bounding boxes.

    Creates masks (numpy arrays) based on image segmentation and bounding boxes from
    object detection (YOLO).

    Returns:
        tuple: List of masks and corresponding scores.
    """
    sam_predictor.set_image(np.array(image))
    masks = []
    scores = []
    for bbox in bounding_boxes:
        mask, score = mask_from_bbox(np.array(bbox), sam_predictor)
        masks.append(mask)
        scores.append(score)
    return masks, scores


def mask_from_bbox(bbox, sam_predictor: SamPredictor) -> tuple:
    """Generate a mask using SAM (Segment Anything) predictor for a given bounding box.

    Returns:
        tuple: Mask and corresponding score.
    """
    masks, scores, _ = sam_predictor.predict(box=bbox, multimask_output=False)
    return masks[0], scores[0]


def create_marking_array(
    masks: list[NDArray],
    colors: list[int],
    image: NDArray,
) -> NDArray:
    """Create a single color marking array based on masks and colors.

    Parameters:
        - masks: List of masks representing markings.
        - colors: List of colors corresponding to each mask.
        - image: Original sketch map frame.

    Returns:
        NDArray: Single color marking array.
    """
    single_color_marking = np.zeros(
        (image.shape[0], image.shape[1]),
        dtype=np.uint8,
    )
    for color, mask in zip(colors, masks):
        single_color_marking[mask] = color
    return single_color_marking
