# -*- coding: utf-8 -*-
"""
Functions to process images of sketch maps and detect markings on them
"""

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageEnhance
from transformers import pipeline

model = "facebook/sam-vit-base"

kwargs = {}


def detect_markings(
        masks,
        rawImage,
        sketch_map_frame: NDArray,
        color: str,
) -> NDArray:
    """
    Detect markings in the colours blue, green, red, pink, turquoise, white, and yellow
    Note that there must be a sufficient difference between the colour of the markings
    and the background. White and yellow markings might not be detected on sketch maps.


    :param sketch_map_frame: TODO
    :param threshold_bgr: Threshold for the colour detection. 0.5 means 50%, i.e. all
                          BGR values above 50% * 255 will be considered 255,
                          all values below this threshold will be considered
                          0 for determining the colour of the markings.
    """
    colors = [average_color_inside_mask(rawImage, mask) for mask in masks]
    masks = [mask for mask, clr in zip(masks, colors) if clr == color]
    single_color_marking = np.zeros_like(sketch_map_frame, np.uint8)
    for mask in masks:
        single_color_marking[mask] = 1
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


def average_color_inside_mask(image, mask):
    # Convert image to NumPy array
    img_array = np.array(image)

    # Extract RGB values of pixels inside the mask
    masked_pixels = img_array[mask]

    # Calculate the average color
    if len(masked_pixels) > 0:
        average_color = np.mean(masked_pixels, axis=0)
        return average_color.astype(np.uint8)  # Convert to integer values
    else:
        return None


def padding(img, padding=-30):
    width, height = img.size

    # Calculate the new image size
    new_width = width + 2 * padding
    new_height = height + 2 * padding

    # Create a new blank image with the new size and a white background
    new_img = Image.new("RGB", (new_width, new_height), (255, 255, 255))

    # Calculate the position to paste the original image with negative padding
    x_offset = padding
    y_offset = padding

    # Paste the original image onto the new image
    new_img.paste(img, (x_offset, y_offset))
    return new_img


def closest_color(rgb_value, threshold=0.5):
    colors = {
        "blue": [0, 0, 255],
        "green": [0, 255, 0],
        "red": [255, 0, 0],
        "pink": [255, 0, 255],
        "turquoise": [0, 255, 255],
        "yellow": [255, 255, 0],
    }
    # Convert the input RGB value to a NumPy array
    target = np.array(rgb_value)

    # Initialize variables for the closest color
    closest_color = None
    closest_distance = float('inf')

    # Iterate through the predefined colors
    for color_name, color_rgb in colors.items():
        color_rgb = np.array(color_rgb)

        # Apply the threshold to the color comparison
        distance = np.linalg.norm(target - color_rgb)

        # Check if this color is closer
        if distance < closest_distance:
            closest_color = color_name
            closest_distance = distance

    return closest_color


def apply_sam(img):
    generator = pipeline("mask-generation", model=model)
    outputs = generator(img, **kwargs)
    masks = outputs["masks"]
    return masks
