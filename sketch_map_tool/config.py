import os
from types import MappingProxyType
from typing import Dict

import toml

from sketch_map_tool.helpers import get_project_root

DEFAULT_CONFIG = {
    "data-dir": str(get_project_root() / "data"),
    "weights-dir": str(get_project_root() / "weights"),
    "user-agent": "sketch-map-tool",
    "broker-url": "redis://localhost:6379",
    "result-backend": "db+postgresql://smt:smt@localhost:5432",
    "cleanup-map-frames-interval": "12 months",
    "wms-url-osm": "https://maps.heigit.org/raster/osm-carto/service?SERVICE=WMS&VERSION=1.1.1",
    "wms-layers-osm": "heigit:osm-carto-proxy",
    "wms-url-esri-world-imagery": "https://maps.heigit.org/raster/sketch-map-tool/service?SERVICE=WMS&VERSION=1.1.1",
    "wms-url-esri-world-imagery-fallback": "https://maps.heigit.org/raster/sketch-map-tool/service?SERVICE=WMS&VERSION=1.1.1",
    "wms-layers-esri-world-imagery": "world_imagery",
    "wms-layers-esri-world-imagery-fallback": "world_imagery_fallback",
    "wms-read-timeout": 600,
    "max-nr-simultaneous-uploads": 100,
    "yolo_cls": "SMT-CLS",
    "yolo_osm_obj": "SMT-OSM",
    "yolo_esri_obj": "SMT-ESRI",
    "model_type_sam": "vit_b",
    "esri-api-key": "",
    "log-level": "INFO",
}


def get_config_path() -> str:
    """Get configuration file path.

    Read value of the environment variable 'SMT_CONFIG'
    or use default 'config/config.toml'.
    """
    default = str(get_project_root() / "config" / "config.toml")
    return os.getenv("SMT_CONFIG", default=default)


def load_config_from_file(path: str) -> Dict[str, str]:
    """Load configuration from file on disk."""
    if os.path.isfile(path):
        with open(path, "r") as f:
            return toml.load(f)
    else:
        return {}


def get_config() -> MappingProxyType:
    """Get configuration variables from environment and file.

    Configuration values from file will be given precedence over default values.
    """
    cfg = DEFAULT_CONFIG
    cfg_file = load_config_from_file(get_config_path())
    cfg.update(cfg_file)
    return MappingProxyType(cfg)


def get_config_value(key: str):
    config = get_config()
    return config[key]
