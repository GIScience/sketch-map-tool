import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageEnhance
from segment_anything import SamPredictor
from ultralytics import YOLO
from ultralytics_4bands import YOLO as YOLO_4


def detect_markings(
    sketch_map_frame: NDArray,
    map_frame: NDArray,
    yolo_obj: YOLO_4,
    yolo_cls: YOLO,
    sam_predictor: SamPredictor,
) -> list[NDArray]:
    """Run machine learning pipeline and post-processing to detect markings.

    The pipeline consists of the following steps:
    1. Apply the machine learning pipeline to given sketch map
    2. Update color indexes since 0 represents the background
    3. Apply post-processing to the results

    Parameters:
    sketch_map_frame: The sketch map frame with markings (clipped uploaded image).
    map_frame: The original map frame without markings.
    yolo_obj: The YOLO model for object detection (multibands version).
    yolo_cls: The YOLO model for classification.
    sam_predictor: The SAM model for segmentation.

    Returns: A list of numpy arrays representing the detected markings.
    """
    # SAM can only deal with RGB (not RGBA)
    image = Image.fromarray(cv2.cvtColor(sketch_map_frame, cv2.COLOR_BGR2RGB))
    difference = get_difference(image, map_frame)
    # masks represent markings
    masks, bboxes, colors = apply_ml_pipeline(
        image,
        difference,
        yolo_obj,
        yolo_cls,
        sam_predictor,
    )
    colors = [int(c) + 1 for c in colors]  # +1 because 0 is background
    processed_markings = post_process(masks, bboxes, colors)
    return processed_markings


def get_difference(
    sketch_map_frame: Image.Image,
    map_frame: NDArray,
    threshold: int = 0,
) -> Image.Image:
    """Difference image between original map frame and sketch map frame.

    Build grayscale image of the absolute difference between map frame
    and the sketch map frame with markings on it.

    The `threshold` parameter is an experimental filtering of
    the markings based on amplitude of the difference.
    """
    image = enhance_contrast(sketch_map_frame)
    difference = cv2.absdiff(map_frame, image)
    difference_gray = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
    # TODO:
    # 1. Pyright: Operator ">" not supported for types "MatLike" and "int"
    #      Operator ">" not supported for types "NumPyArrayGeneric" and "int"
    #      [reportGeneralTypeIssues]
    mask_markings = difference_gray > threshold
    difference_gray = difference_gray * mask_markings
    difference_gray = Image.fromarray(difference_gray)
    return difference_gray


def enhance_contrast(image: Image.Image, factor: float = 2.0) -> NDArray:
    """Enhance the contrast of a given image."""
    result = ImageEnhance.Contrast(image).enhance(factor)
    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)


def apply_ml_pipeline(
    image: Image.Image,
    difference: Image.Image,
    yolo_obj: YOLO_4,
    yolo_cls: YOLO,
    sam_predictor: SamPredictor,
) -> tuple[list[NDArray], NDArray, list]:
    """Apply the entire machine learning pipeline on an image.

    Steps:
        1. Apply YOLO object detection to detect bounding boxes of objects (markings)
        2. Apply YOLO classification on bbox level images to classify labels
        3. Apply SAM to create binary masks of detected objects

    Returns:
        tuple: A list of masks and class labels.
            Masks are binary numpy arrays with same dimensions as input image
            (map frame), masking the dominant segment inside of a bbox detected by YOLO.
            Class labels are colors.
    """
    bounding_boxes, _ = apply_yolo_object_detection(image, difference, yolo_obj)
    colors = apply_yolo_classification(image, bounding_boxes, yolo_cls)
    masks, _ = apply_sam(image, bounding_boxes, sam_predictor)
    return masks, bounding_boxes, colors


def apply_yolo_object_detection(
    image: Image.Image,
    difference: Image.Image,
    yolo: YOLO_4,
) -> tuple[NDArray, NDArray]:
    """Apply fine-tuned YOLO object detection on an image.

    Returns:
        tuple: Detected bounding boxes around individual markings and corresponding
        class labels (colors).
    """
    image = Image.merge("RGBA", (*image.split(), difference))
    result = yolo.predict(image)[0].boxes  # TODO set conf parameter
    bounding_boxes = result.xyxy.numpy()
    class_labels = result.cls.numpy()
    return bounding_boxes, class_labels


def apply_yolo_classification(
    image: Image.Image,
    bounding_boxes: NDArray,
    yolo: YOLO,
) -> list:
    """Apply fine-tuned YOLO image classification on a bounding box level image
    to detect marking characteristics
    (color, marking_type).

    Returns: list of labels predicted by the model.
    """
    labels = []
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    for b in bounding_boxes:
        x_min, y_min, x_max, y_max = [int(i) for i in b[:4]]
        cropped_image = img[y_min:y_max, x_min:x_max]
        res = yolo(
            Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
        )
        # get names from the model and label append to the list
        labels.append(res[0].probs.top1)
    return labels


def apply_sam(
    image: Image.Image,
    bounding_boxes: NDArray,
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


def mask_from_bbox(
    bbox: NDArray,
    sam_predictor: SamPredictor,
) -> tuple:
    """Generate a mask using SAM (Segment Anything) predictor for a given bounding box.

    Returns:
        tuple: Mask and corresponding score.
    """
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
    bboxes: NDArray,
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
