import os
from types import MappingProxyType
from typing import Dict

import toml

from sketch_map_tool.helpers import get_project_root


def get_config_path() -> str:
    """Get configuration file path

    Read value of the environment variable 'SMT_CONFIG' or use default 'config.toml'
    """
    default = str(get_project_root() / "config" / "config.toml")
    return os.getenv("SMT_CONFIG", default=default)


def load_config_default() -> Dict[str, str | int | float]:
    return {
        "data-dir": get_default_data_dir(),
        "user-agent": "sketch-map-tool",
        "broker-url": "redis://localhost:6379",
        "result-backend": "db+postgresql://smt:smt@localhost:5432",
        "wms-url-osm": "https://maps.heigit.org/osm-carto/service?SERVICE=WMS&VERSION=1.1.1",
        "wms-layers-osm": "heigit:osm-carto@2xx",
        "wms-url-esri-world-imagery": "https://maps.heigit.org/sketch-map-tool/service?SERVICE=WMS&VERSION=1.1.1",
        "wms-layers-esri-world-imagery": "world_imagery",
        "wms-read-timeout": 600,
        "max-nr-simultaneous-uploads": 100,
        "max_pixel_per_image": 10e8,  # 10.000*10.000
        "neptune_project": "HeiGIT/SketchMapTool",
        "neptune_api_token": "",
        "neptune_model_id_yolo_osm_cls": "SMT-CLR-1",
        "neptune_model_id_yolo_esri_cls": "SMT-CLR-3",
        "neptune_model_id_yolo_osm_obj": "SMT-OSM-9",
        "neptune_model_id_yolo_esri_obj": "SMT-ESRI-1",
        "neptune_model_id_sam": "SMT-SAM-1",
        "model_type_sam": "vit_b",
        "esri-api-key": "",
        "log-level": "INFO",
    }


def load_config_from_file(path: str) -> Dict[str, str]:
    """Load configuration from file on disk."""
    if os.path.isfile(path):
        with open(path, "r") as f:
            return toml.load(f)
    else:
        return {}


def load_config_from_env() -> Dict[str, str]:
    """Load configuration from environment variables."""
    cfg = {
        "data-dir": os.getenv("SMT_DATA_DIR"),
        "user-agent": os.getenv("SMT_USER_AGENT"),
        "broker-url": os.getenv("SMT_BROKER_URL"),
        "result-backend": os.getenv("SMT_RESULT_BACKEND"),
        "wms-url-osm": os.getenv("SMT_WMS_URL"),
        "wms-layers-osm": os.getenv("SMT_WMS_LAYERS"),
        "wms-url-esri-world-imagery": os.getenv("SMT_WMS_URL_ESRI_WORLD_IMAGERY"),
        "wms-layers-esri-world-imagery": os.getenv("SMT_WMS_LAYERS_ESRI_WORLD_IMAGERY"),
        "wms-read-timeout": os.getenv("SMT_WMS_READ_TIMEOUT"),
        "max-nr-simultaneous-uploads": os.getenv("SMT_MAX_NR_SIM_UPLOADS"),
        "max_pixel_per_image": os.getenv("SMT_MAX_PIXEL_PER_IMAGE"),
        "neptune_project": os.getenv("SMT_NEPTUNE_PROJECT"),
        "neptune_api_token": os.getenv("SMT_NEPTUNE_API_TOKEN"),
        "neptune_model_id_sam": os.getenv("SMT_NEPTUNE_MODEL_ID_SAM"),
        "model_type_sam": os.getenv("SMT_MODEL_TYPE_SAM"),
        "esri-api-key": os.getenv("SMT_ESRI_API_KEY"),
        "log-level": os.getenv("SMT_LOG_LEVEL"),
    }

    return {k: v for k, v in cfg.items() if v is not None}


def get_config() -> MappingProxyType:
    """Get configuration variables from environment and file.

    Configuration values from file will be given precedence over default vaules.
    Configuration values from environment variables will be given precedence over file
    values.
    """
    cfg = load_config_default()
    cfg_file = load_config_from_file(get_config_path())
    cfg_env = load_config_from_env()
    cfg.update(cfg_file)
    cfg.update(cfg_env)
    return MappingProxyType(cfg)


def get_config_value(key: str) -> str:
    config = get_config()
    return config[key]


def get_default_data_dir() -> str:
    return str(get_project_root() / "data")
