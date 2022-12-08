# -*- coding: utf-8 -*-
"""
Functions to process images of sketch maps and detect markings on them
"""
from typing import List, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageEnhance


def detect_markings(
    img_base: NDArray,
    img_markings: NDArray,
    colour: str,
    hsv_interval_size: int = 40,
    threshold_img_diff: int = 150,
) -> List[Tuple[str, NDArray]]:
    """
    Detect markings in the colours blue, green, red, pink, turquoise, white, and yellow.
    Note that there must be a sufficient difference between the colour of the markings
    and the background. White and yellow markings might therefore not be detected on many
    sketch maps.


    :param img_base: Map without markings.
    :param img_markings: Map with markings.
    :param colour: Colour of the markings to be detected.
    :param hsv_interval_size: Size of the H-value interval to be used. 40 means +/- 20 around
                              the defined value for the chosen colour 'colour'.
    :param threshold_img_diff: Threshold for the marking detection concerning the absolute
                               grayscale difference between corresponding pixels in 'img_base' and
                               'img_markings'.
    :return: A list of pairs of the colour name and the image object with the detected markings in
             this colour [("colour name", img_array), ...].
    """
    # For the colour detection see https://docs.opencv.org/3.4/df/d9d/tutorial_py_colorspaces.html
    # under "How to find HSV values to track?"
    # Tests have shown that an H-value interval of +/- 20, i.e. a size of 40, works better
    # than +/- 10
    # To test out different HSV ranges, you can use the code snippet under
    # https://stackoverflow.com/a/59906154

    # Calculate HSV values based on BGR colour values:
    colors = {
        "red": cv2.cvtColor(np.uint8([[[0, 0, 255]]]), cv2.COLOR_BGR2HSV),
        "blue": cv2.cvtColor(np.uint8([[[255, 0, 0]]]), cv2.COLOR_BGR2HSV),
        "green": cv2.cvtColor(np.uint8([[[0, 255, 0]]]), cv2.COLOR_BGR2HSV),
    }
    if colour not in colors.keys():
        raise ValueError(f"Colour {colour} is not supported yet.")
    hsv = colors[colour]

    # Calculate the H-value interval of the colour given as argument
    h_value_interval = hsv[0][0][0] - int(hsv_interval_size / 2), hsv[0][0][0] + int(
        hsv_interval_size / 2
    )

    # In case one of the values lies outside the range (0, 179), the interval has to be adjusted
    if h_value_interval[0] < 0:
        h_value_interval = (179 + h_value_interval[0], 179)
        # The second interval (0, h_value_interval[1]) has been discarded as currently this is only
        # relevant for red and matches an orange typically used in OSM icons resulting in much noise
    elif h_value_interval[1] > 179:
        h_value_interval = (h_value_interval[0], 179)
        # Currently not the case, when more colours are added, please check whether the second
        # possible interval needs to be considered.
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
    markings_multicolor = cv2.cvtColor(markings_multicolor, cv2.COLOR_BGR2HSV)
    single_color_marking = np.zeros_like(markings_multicolor, np.uint8)
    single_color_marking[
        ((markings_multicolor[:, :, 0] >= h_value_interval[0]))
        & ((markings_multicolor[:, :, 0] <= h_value_interval[1]))
        & ((markings_multicolor[:, :, 1] >= 100))
        & ((markings_multicolor[:, :, 2] >= 100))
    ] = 255

    single_color_marking = _reduce_noise(single_color_marking)
    single_color_marking = _reduce_holes(single_color_marking)
    single_color_marking[single_color_marking > 0] = 255
    return single_color_marking


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
