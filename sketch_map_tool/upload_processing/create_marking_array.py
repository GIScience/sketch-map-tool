import numpy as np
from numpy._typing import NDArray


def create_marking_array(
    masks: list[NDArray],
    colors: list[int],
    image: NDArray,
) -> NDArray:
    """Create a single color marking array based on masks and colors.

    Parameters:
        - masks: List of masks representing markings.
        - colors: List of colors corresponding to each mask.
        - image: Original sketch map frame.

    Returns:
        NDArray: Single color marking array.
    """
    single_color_marking = np.zeros(
        (image.shape[0], image.shape[1]),
        dtype=np.uint8,
    )
    for color, mask in zip(colors, masks):
        single_color_marking[mask] = color
    return single_color_marking
