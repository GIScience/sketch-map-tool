import logging
from pathlib import Path

import neptune

from sketch_map_tool.config import get_config_value

PROJECT = get_config_value("neptune_project")
API_TOKEN = get_config_value("neptune_api_token")


def init_model(id: str) -> Path:
    """Initilaze model. Download model to data dir if not present."""
    # TODO:
    # _check_id(id)

    data_dir = Path(get_config_value("data-dir"))
    # TODO: first check if model is on disk
    # if so return model without connecting to neptune.ai
    model = neptune.init_model_version(
        with_id=id,
        project=PROJECT,
        api_token=API_TOKEN,
        mode="read-only",
    )

    raw = data_dir / id
    path = raw.with_suffix(_get_file_suffix(id))
    if not path.is_file():
        logging.info(f"Downloading model {id} from neptune.ai to {path}.")
        model["model"].download(str(path))

    # TODO: check if model is valid/working
    logging.info("Available model from neptune.ai on disk: " + id)
    return path


def _check_id(id: str):
    # TODO:
    project = neptune.init_project(
        project=PROJECT,
        api_token=API_TOKEN,
        mode="read-only",
    )

    if not project.exists("models/" + id):
        raise ValueError("Invalid model ID: " + id)


def _get_file_suffix(id: str) -> str:
    if "SAM" in id:
        return ".pth"
    elif "OSM" in id:
        return ".pt"
    else:
        raise ValueError("Unexpected model ID: " + id)
