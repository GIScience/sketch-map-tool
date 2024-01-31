# -*- coding: utf-8 -*-
import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image
from segment_anything import SamPredictor
from ultralytics import YOLO


def detect_markings(
    image: NDArray,
    yolo_model: YOLO,
    sam_predictor: SamPredictor,
) -> list[NDArray]:
    # SAM can only deal with RGB and not RGBA etc.
    img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # masks represent markings
    masks, bboxes, colors = apply_ml_pipeline(img, yolo_model, sam_predictor)
    colors = [int(c) + 1 for c in colors]  # +1 because 0 is background
    processed_markings = post_process(masks, bboxes, colors)
    return processed_markings


def apply_ml_pipeline(
    image: Image.Image,
    yolo_model: YOLO,
    sam_predictor: SamPredictor,
) -> tuple[list[NDArray], NDArray, NDArray]:
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
    return masks, bounding_boxes, class_labels


def apply_yolo(
    image: Image.Image,
    yolo_model: YOLO,
) -> tuple[NDArray, NDArray]:
    """Apply fine-tuned YOLO object detection on an image.

    Returns:
        tuple: Detected bounding boxes around individual markings and corresponding
        class labels (colors).
    """
    result = yolo_model(image, conf=0.7)[0].boxes  # TODO set conf parameter
    bounding_boxes = result.xyxy.numpy()
    class_labels = result.cls.numpy()
    return bounding_boxes, class_labels


def apply_sam(
    image: Image.Image,
    bounding_boxes: list,
    sam_predictor: SamPredictor,
) -> tuple[list[NDArray], list[np.float32]]:
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
        mask, score = mask_from_bbox(bbox, sam_predictor)
        masks.append(mask)
        scores.append(score)
    return masks, scores


def mask_from_bbox(bbox: NDArray, sam_predictor: SamPredictor) -> tuple:
    """Generate a mask using SAM (Segment Anything) predictor for a given bounding box.

    Returns:
        tuple: Mask and corresponding score.
    """
    breakpoint()
    masks, scores, _ = sam_predictor.predict(box=bbox, multimask_output=False)
    return masks[0], scores[0]


def create_marking_array(
    mask: NDArray,
    color: int,
) -> NDArray:
    """Create a single color marking array based on masks and colors."""
    single_color_marking = np.zeros(mask.shape, dtype=np.uint8)
    single_color_marking[mask] = color
    return single_color_marking


def post_process(
    masks: list[NDArray],
    bboxes: list[list[int]],
    colors: list,
) -> list[NDArray]:
    """Post-processes masks and bounding boxes to clean-up and fill contours.

    Apply morphological operations to clean the masks, creates contours and fills them.
    """
    # Convert and preprocess masks
    preprocessed_masks = np.array([np.vstack(mask) for mask in masks], dtype=np.float32)
    preprocessed_masks[preprocessed_masks == 0] = np.nan

    # Calculate height and width for each bounding box
    bbox_sizes = [np.array([bbox[2] - bbox[0], bbox[3] - bbox[1]]) for bbox in bboxes]

    processed_markings = []
    for i, (mask, color) in enumerate(zip(preprocessed_masks, colors)):
        # Calculate kernel size as 5% of the bounding box dimensions
        kernel_size = tuple((bbox_sizes[i] * 0.05).astype(int))
        kernel = np.ones(kernel_size, np.uint8)

        # Apply morphological closing operation
        mask_closed = cv2.morphologyEx(mask.astype("uint8"), cv2.MORPH_CLOSE, kernel)

        # Find contours
        mask_contour, _ = cv2.findContours(
            mask_closed,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        # Create a blank canvas for filled contours
        mask_filled = np.zeros_like(mask_closed, dtype=np.uint8)
        cv2.drawContours(mask_filled, mask_contour, -1, 1, thickness=cv2.FILLED)

        # Mask to markings array
        processed_markings.append(create_marking_array(mask_filled.astype(bool), color))
    return processed_markings
