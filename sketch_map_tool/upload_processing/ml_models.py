import logging
from pathlib import Path

import neptune
import requests
import torch
from torch._prims_common import DeviceLikeType

from sketch_map_tool.config import get_config_value


def init_model(id: str) -> Path:
    """Initialize model. Download model to data dir if not present."""
    raw = Path(get_config_value("data-dir")) / id
    path = raw.with_suffix(".pt")
    if not path.is_file():
        logging.info(f"Downloading model {id} from neptune.ai to {path}.")
        model = neptune.init_model_version(
            with_id=id,
            project=get_config_value("neptune_project"),
            api_token=get_config_value("neptune_api_token"),
            mode="read-only",
        )
        model["model"].download(str(path))
    return path


def init_sam2(id: str = "sam2_hiera_base_plus") -> Path:
    raw = Path(get_config_value("data-dir")) / id
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
