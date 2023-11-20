# -*- coding: utf-8 -*-
"""
Functions to process images of sketch maps and detect markings on them
"""


import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageEnhance

from ultralytics import YOLO
from segment_anything import sam_model_registry
from segment_anything import SamPredictor

from sketch_map_tool.upload_processing.ml_models import init_model
from sketch_map_tool.config import  get_config_value

sam = sam_model_registry["vit_b"](init_model(get_config_value("neptune_model_id_sam")))

mask_predictor = SamPredictor(sam)

modelYOLO = YOLO(init_model(get_config_value("neptune_model_id_yolo")))
names = modelYOLO.names


def createMarkingArray(
        masks: list[NDArray],
        colors: list[str],
        sketch_map_frame: NDArray,
) -> NDArray:
    single_color_marking = np.zeros((sketch_map_frame.shape[0],sketch_map_frame.shape[1]), np.uint8)
    for color,mask in zip(colors,masks):
        single_color_marking[mask] = color
    return single_color_marking

def prepare_img_for_markings(
        img_base: NDArray,
        img_markings: NDArray,
        id: int,
        threshold_img_diff: int = 100,
) -> NDArray:
    """
    TODO pydoc

    :param threshold_img_diff: Threshold for the marking detection concerning the
    absolute grayscale difference between corresponding pixels
    in 'img_base' and 'img_markings'.
    """
    img_base_height, img_base_width, _ = img_base.shape
    img_markings = cv2.resize(
        img_markings,
        (img_base_width, img_base_height),
        fx=4,
        fy=4,
        interpolation=cv2.INTER_NEAREST,
    )
    img_markings_contrast = _enhance_contrast(img_markings)
    img_diff = cv2.absdiff(img_base, img_markings_contrast)
    img_diff_gray = cv2.cvtColor(img_diff, cv2.COLOR_BGR2GRAY)
    mask_markings = img_diff_gray > threshold_img_diff
    markings_multicolor = np.zeros_like(img_markings, np.uint8)
    markings_multicolor[mask_markings] = img_markings[mask_markings]

    return markings_multicolor


def _enhance_contrast(img: NDArray, factor: float = 2.0) -> NDArray:
    """
    Enhance the contrast of a given image

    :param img: Image of which the contrast should be enhanced.
    :param factor: Factor for the contrast enhancement.
    :return: Image with enhanced contrast.
    """
    input_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    result = ImageEnhance.Contrast(input_img).enhance(factor)
    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)


def _reduce_noise(img: NDArray, factor: int = 2) -> NDArray:
    """
    Reduce the noise, i.e. artifacts, in an image containing markings

    :param img: Image in which the noise should be reduced.
    :param factor: Kernel size (x*x) for the noise reduction.
    :return: 'img' with less noise.
    """
    # See https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    reduced_noise = cv2.morphologyEx(
        img, cv2.MORPH_OPEN, np.ones((factor, factor), np.uint8)
    )
    # TODO: Long running job in next line -> Does the slightly improved noise
    #       reduction justify keeping it?
    return cv2.fastNlMeansDenoisingColored(reduced_noise, None, 30, 30, 20, 21)


def _reduce_holes(img: NDArray, factor: int = 4) -> NDArray:
    """
    Reduce the holes in markings on a given image

    :param img: Image in which the holes should be reduced.
    :param factor: Kernel size (x*x) of the reduction.
    :return: 'img' with fewer and smaller holes.
    """
    # See https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((factor, factor), np.uint8))


def applyYOLO(image, yolo):
    result = yolo(image)[0].boxes
    bboxes = result.xyxy
    cls = result.cls
    return bboxes, cls


def maskFromBBox(box, mask_predictor):
    masks, scores, logits = mask_predictor.predict(
        box=box,
        multimask_output=False
    )
    return masks[0], scores[0]


def applySAM(image, bboxes, mask_predictor):
    mask_predictor.set_image(np.array(image))
    masks = []
    scores = []

    for box in bboxes:
        mask, score = maskFromBBox(np.array(box), mask_predictor)
        masks.append(mask)
        scores.append(score)
    return masks, scores


def applyMLPipeline(img):
    bboxes, cls = applyYOLO(img, modelYOLO)
    masks, scores = applySAM(img, bboxes, mask_predictor)
    colors = [names[i] for i in cls]
    return masks, colors
