"""
Functionality to cut a sketch map out of a photograph containing one,
based on a matching template
"""
import cv2
import numpy as np
from numpy.typing import NDArray


def filter_matrix(tran_matrix: NDArray) -> bool:
    """Filters a failed transformation matrix based on specified conditions."""
    h13 = tran_matrix[0, 2]
    h23 = tran_matrix[1, 2]

    if h13 > 1500 and h23 > 0:
        return False
    else:
        return True


def clip(photo: NDArray, template: NDArray) -> NDArray:
    """Clip out the map frame from the photo of the map using the original map frame.

    Use the BRISK implementation in OpenCV to detect a map on a given
    photo based on a given template with the map. The detected area of the
    image is warped to have the same alignment as the template.

    Utilizes the FLANN (Fast Library for Approximate Nearest Neighbors)
    algorithm for efficient
    descriptor matching.

    :param photo: Photograph of a sketch map
    :param template: Matching template of the sketch map
    :return: The resulting image (the cutout)
    """
    brisk = cv2.BRISK_create()

    # Convert images to grayscale
    photo_gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # Detect keypoints and compute descriptors
    kpts1, desc1 = brisk.detectAndCompute(photo_gray, None)
    kpts2, desc2 = brisk.detectAndCompute(template_gray, None)

    # FLANN parameters
    flann_params = {
        "algorithm": 6,
        "table_number": 6,
        "key_size": 12,
        "multi_probe_level": 1,
    }

    # FLANN matcher
    matcher = cv2.FlannBasedMatcher(flann_params, {})
    matches = matcher.knnMatch(queryDescriptors=desc1, trainDescriptors=desc2, k=2)

    # Filter good matches
    good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]

    # Extract corresponding points
    src_pts = np.float32([kpts1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kpts2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # Find homography matrix
    homography_matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)
    # Get dimensions of template
    height, width, _ = template.shape

    # Check if homography matrix passes filter
    succeed = filter_matrix(homography_matrix)

    # Warp perspective if homography matrix passes filter
    if succeed:
        selected_map = cv2.warpPerspective(photo, homography_matrix, (width, height))
    else:
        selected_map = np.zeros((width, height))

    return selected_map
