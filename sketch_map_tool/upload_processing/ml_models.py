import logging
from pathlib import Path

import requests
import torch
from torch._prims_common import DeviceLikeType

from sketch_map_tool.config import CONFIG


def init_model(id: str) -> Path:
    """Initialize model. Raise error if not found."""
    raw = Path(CONFIG.weights_dir) / id
    path = raw.with_suffix(".pt")
    if not path.is_file():
        raise FileNotFoundError("Model not found at " + str(path))
    return path


def init_sam2(id: str = "sam2_hiera_base_plus") -> Path:
    raw = Path(CONFIG.weights_dir) / id
    path = raw.with_suffix(".pt")
    base_url = "https://dl.fbaipublicfiles.com/segment_anything_2/072824/"
    url = base_url + id + ".pt"
    if not path.is_file():
        logging.info(f"Downloading model SAM-2 from fbaipublicfiles.com to {path}.")
        response = requests.get(url=url)
        with open(path, mode="wb") as file:
            file.write(response.content)
    return path


def select_computation_device() -> DeviceLikeType:
    """Select computation device (cuda, mps, cpu) for SAM-2"""
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    logging.info(f"Using device: {device}")

    if device.type == "cuda":
        # use bfloat16 for the entire notebook
        torch.autocast("cuda", dtype=torch.bfloat16).__enter__()
        # turn on tfloat32 for Ampere GPUs
        if torch.cuda.get_device_properties(0).major >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
    return device
