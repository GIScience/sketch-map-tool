"""Load configuration from environment variables or configuration file on disk."""

import os
from types import MappingProxyType
from typing import Dict

import toml

from sketch_map_tool.helpers import get_project_root


def get_config_path() -> str:
    """Get configuration file path

    Read value of the environment variable 'OQT-CONFIG' or use default 'config.toml'
    """
    default = str(get_project_root() / "config" / "config.toml")
    return os.getenv("SMT-CONFIG", default=default)


def load_config_default() -> Dict[str, str]:
    return {
        "data-dir": get_default_data_dir(),
        "user-agent": "sketch-map-tool",
        "broker-url": "redis://localhost:6379",
        "result-backend": "db+postgresql://smt:smt@localhost:5432",
        "data-store": "redis://localhost:6379",
        "wms-url": "https://maps.heigit.org/osm-carto/service?SERVICE=WMS&VERSION=1.1.1",
        "wms-layers": "heigit:osm-carto@2xx",
        "wms-read-timeout": 600,
        "max-nr-simultaneous-uploads": 100,
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
        "data-dir": os.getenv("SMT-DATA-DIR"),
        "user-agent": os.getenv("SMT-USER-AGENT"),
        "broker-url": os.getenv("SMT-BROKER-URL"),
        "result-backend": os.getenv("SMT-RESULT-BACKEND"),
        "data-store": os.getenv("SMT-DATA-STORE"),
        "wms-url": os.getenv("SMT-WMS-URL"),
        "wms-layers": os.getenv("SMT-WMS-LAYERS"),
        "wms-read-timeout": os.getenv("SMT-WMS-READ-TIMEOUT"),
        "max-nr-simultaneous-uploads": os.getenv("SMT-MAX-NR-SIM-UPLOADS"),
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
