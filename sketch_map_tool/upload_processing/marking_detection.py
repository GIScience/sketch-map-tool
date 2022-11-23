# -*- coding: utf-8 -*-
"""
Functions to process images of sketch maps and detect markings on them
"""
import numpy as np
from numpy.typing import NDArray
from PIL import ImageEnhance, ImageChops, Image
import cv2


def enhance_contrast(img: NDArray, factor: float = 2.0) -> NDArray:
    """
    Enhance the contrast of a given image

    :param img: Image of which the contrast should be enhanced
    :param factor: Factor for the contrast enhancement
    :return: Image with enhanced contrast
    """
    input_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    result = ImageEnhance.Contrast(input_img).enhance(factor)
    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)


def detect_markings(img_base, img_markings, threshold_bgr=0.5, threshold_img_diff=100):
    # threshold_bgr = 0.5  # 50%, i.e. 255*50% = 127

    threshold_bgr_abs = threshold_bgr * 255

    colors = {"white": (255, 255, 255),
              "red": (0, 0, 255),
              "blue": (255, 0, 0),
              "green": (0, 255, 0),
              "yellow": (0, 255, 255),
              "turquoise": (255, 255, 0),
              "pink": (255, 0, 255)
              }

    img_base_height, img_base_width, _ = img_base.shape
    img_markings = cv2.resize(img_markings, (img_base_width, img_base_height))
    img_markings_contrast = enhance_contrast(img_markings)
    img_diff = cv2.absdiff(img_base, img_markings_contrast)

    img_diff_gray = cv2.cvtColor(img_diff, cv2.COLOR_BGR2GRAY)
    mask_markings = img_diff_gray > threshold_img_diff
    markings_unicolor = np.zeros_like(img_diff, np.uint8)
    markings_unicolor[mask_markings] = 255
    markings_multicolor = np.zeros_like(img_markings, np.uint8)
    markings_multicolor[mask_markings] = img_markings[mask_markings]

    single_color_markings = []
    for color, bgr in colors.items():
        single_color_marking = np.zeros_like(markings_multicolor, np.uint8)
        single_color_marking[((markings_multicolor[:, :, 0] < threshold_bgr_abs) == (bgr[0] < threshold_bgr_abs)) &
                             ((markings_multicolor[:, :, 1] < threshold_bgr_abs) == (bgr[1] < threshold_bgr_abs)) &
                             ((markings_multicolor[:, :, 2] < threshold_bgr_abs) == (bgr[2] < threshold_bgr_abs))] = 255
        # (markings_multicolor[:, :, 2] > threshold_bgr*255)] = 255
        single_color_markings.append([color, single_color_marking])

    cv2.imwrite("output/markings_all_unicolor.png", markings_unicolor)
    cv2.imwrite("output/markings_all_multicolor.png", markings_multicolor)
    for i in range(len(single_color_markings)):
        single_color_markings[i][1] = reduce_holes(reduce_noise(single_color_markings[i][1]))
    return single_color_markings


def reduce_noise(img: NDArray, factor=2):
    """
    Reduce the noise, i.e. artifacts, in an image containing markings

    :param img: Image in which the noise should be reduced
    :param factor: Strength of the noise reduction
    :return: 'img' with less noise
    """
    # See https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    return cv2.morphologyEx(img, cv2.MORPH_OPEN, np.ones((factor, factor), np.uint8))


def reduce_holes(img: NDArray, factor=5):
    """
    Reduce the holes in markings on a given image

    :param img: Image in which the holes should be reduced
    :param factor: Strength of the reduction
    :return: 'img' with less and smaller holes
    """
    # See https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((factor, factor), np.uint8))
