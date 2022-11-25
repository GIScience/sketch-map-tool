# -*- coding: utf-8 -*-
"""
Functions to process images of sketch maps and detect markings on them
"""
from typing import List, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageEnhance


def enhance_contrast(img: NDArray, factor: float = 2.0) -> NDArray:
    """
    Enhance the contrast of a given image

    :param img: Image of which the contrast should be enhanced.
    :param factor: Factor for the contrast enhancement.
    :return: Image with enhanced contrast.
    """
    input_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    result = ImageEnhance.Contrast(input_img).enhance(factor)
    return cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)


def detect_markings(
    img_base: NDArray,
    img_markings: NDArray,
    threshold_bgr: float = 0.5,
    threshold_img_diff: int = 100,
) -> List[Tuple[str, NDArray]]:
    """
    Detect markings in the colours blue, green, red, pink, turquoise, white, and yellow.
    Note that there must be a sufficient difference between the colour of the markings and the background. White and
    yellow markings might therefore not be detected on many sketch maps.


    :param img_base: Map without markings.
    :param img_markings: Map with markings.
    :param threshold_bgr: Threshold for the colour detection. 0.5 means 50%, i.e. all BGR values above 50% * 255 will be
                          considered 255, all values below this threshold will be considered 0 for determining the
                          colour of the markings.
    :param threshold_img_diff: Threshold for the marking detection concerning the absolute grayscale difference between
                               corresponding pixels in 'img_base' and 'img_markings'.
    :return: A list of pairs of the colour name and the image object with the detected markings in this colour
             [("colour name", img_array), ...].
    """
    threshold_bgr_abs = threshold_bgr * 255

    colors = {
        "white": (255, 255, 255),
        "red": (0, 0, 255),
        "blue": (255, 0, 0),
        "green": (0, 255, 0),
        "yellow": (0, 255, 255),
        "turquoise": (255, 255, 0),
        "pink": (255, 0, 255),
    }

    img_base_height, img_base_width, _ = img_base.shape
    img_markings = cv2.resize(
        img_markings,
        (img_base_width, img_base_height),
        fx=4,
        fy=4,
        interpolation=cv2.INTER_NEAREST,
    )
    img_markings_contrast = enhance_contrast(img_markings)
    img_diff = cv2.absdiff(img_base, img_markings_contrast)

    img_diff_gray = cv2.cvtColor(img_diff, cv2.COLOR_BGR2GRAY)
    mask_markings = img_diff_gray > threshold_img_diff

    markings_multicolor = np.zeros_like(img_markings, np.uint8)
    markings_multicolor[mask_markings] = img_markings[mask_markings]

    single_color_markings = []
    for color, bgr in colors.items():
        single_color_marking = np.zeros_like(markings_multicolor, np.uint8)
        single_color_marking[
            (
                (markings_multicolor[:, :, 0] < threshold_bgr_abs)
                == (bgr[0] < threshold_bgr_abs)
            )
            & (
                (markings_multicolor[:, :, 1] < threshold_bgr_abs)
                == (bgr[1] < threshold_bgr_abs)
            )
            & (
                (markings_multicolor[:, :, 2] < threshold_bgr_abs)
                == (bgr[2] < threshold_bgr_abs)
            )
        ] = 255
        single_color_markings.append(
            (color, reduce_holes(reduce_noise(single_color_marking)))
        )

    return single_color_markings


def reduce_noise(img: NDArray, factor: int = 2) -> NDArray:
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


def reduce_holes(img: NDArray, factor: int = 4) -> NDArray:
    """
    Reduce the holes in markings on a given image

    :param img: Image in which the holes should be reduced.
    :param factor: Kernel size (x*x) of the reduction.
    :return: 'img' with fewer and smaller holes.
    """
    # See https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
    return cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((factor, factor), np.uint8))
