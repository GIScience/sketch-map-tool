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
    single_color_marking = np.zeros((sketch_map_frame.shape[0], sketch_map_frame.shape[1]), np.uint8)
    for color, mask in zip(colors, masks):
        single_color_marking[mask] = color
    return single_color_marking


def applyYOLO(image: Image, yolo: YOLO):
    result = yolo(image)[0].boxes
    bboxes = result.xyxy
    cls = result.cls
    return bboxes, cls


def maskFromBBox(box, mask_predictor: SamPredictor):
    masks, scores, logits = mask_predictor.predict(
        box=box,
        multimask_output=False
    )
    return masks[0], scores[0]


def applySAM(image: Image, bboxes: list, mask_predictor: SamPredictor):
    mask_predictor.set_image(np.array(image))
    masks = []
    scores = []
    for i, box in enumerate(bboxes):
        mask, score = maskFromBBox(np.array(box), mask_predictor)
        masks.append(mask)
        scores.append(score)
    return masks, scores

def applyMLPipeline(img: Image, modelYOLO: YOLO, mask_predictor: SamPredictor):

    bboxes, cls = applyYOLO(img, modelYOLO)
    masks, scores = applySAM(img, bboxes, mask_predictor)
    return masks, cls
