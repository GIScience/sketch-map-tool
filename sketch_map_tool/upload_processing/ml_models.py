import logging
from pathlib import Path

import neptune

from sketch_map_tool.config import get_config_value


def init_model(id: str) -> Path:
    """Initialize model. Download model to data dir if not present."""
    # TODO: _check_id(id)
    # TODO: check if model is valid/working
    raw = Path(get_config_value("data-dir")) / id
    path = raw.with_suffix(_get_file_suffix(id))
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
    return path


def _check_id(id: str):
    # TODO:
    project = neptune.init_project(
        project=get_config_value("neptune_project"),
        api_token=get_config_value("neptune_api_token"),
        mode="read-only",
    )

    if not project.exists("models/" + id):
        raise ValueError("Invalid model ID: " + id)


def _get_file_suffix(id: str) -> str:
    suffixes = {"SAM": ".pth", "OSM": ".pt", "ESRI": ".pt", "CLR": ".pt"}

    for key in suffixes:
        if key in id:
            return suffixes[key]

    raise ValueError(f"Unexpected model ID: {id}")
