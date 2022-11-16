"""
Functionality to cut a sketch map out of a photograph containing one,
based on a matching template
"""
from typing import Any

import cv2
import numpy as np


def cut_out_map(
    photo: "np.ndarray[Any, np.dtype[np.int64]]",
    template: "np.ndarray[Any, np.dtype[np.int64]]",
) -> "np.ndarray[Any, np.dtype[np.int64]]":
    """
    Use the BRISK implementation in OpenCV to detect a map on a given
    photo based on a given template with the map. The detected area of the
    image is warped to have the same alignment as the template.

    :param photo: Photograph of a sketch map
    :param template: Matching template of the sketch map
    :return: The resulting image (the cutout)
    """
    brisk = cv2.BRISK_create()
    photo_gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)

    kpts1, desc1 = brisk.detectAndCompute(photo_gray, None)
    kpts2, desc2 = brisk.detectAndCompute(template, None)

    matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
    matches = list(matcher.match(desc1, desc2, None))
    matches.sort(key=lambda x: x.distance, reverse=False)
    good_matches = matches[0 : round(len(matches) * 0.05)]
    src_pts = np.float32([kpts1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kpts2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    homography_matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)
    height, width, _ = template.shape
    selected_map = cv2.warpPerspective(photo, homography_matrix, (width, height))
    return selected_map
