import logging
import os

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from sketch_map_tool.helpers import get_project_root


def get_config_path() -> str:
    """Get configuration file path.

    Read value of the environment variable 'SMT_CONFIG'
    or use default 'config/config.toml'.
    """
    default = str(get_project_root() / "config" / "config.toml")
    return os.getenv("SMT_CONFIG", default=default)


class Config(BaseSettings):
    broker_url: str = "redis://localhost:6379"
    cleanup_map_frames_interval: str = "12 months"
    data_dir: str = str(get_project_root() / "data")  # TODO: make this a Path
    esri_api_key: str = ""
    log_level: str = "INFO"
    max_nr_simultaneous_uploads: int = 100
    model_type_sam: str = "configs/sam2.1/sam2.1_hiera_l.yaml"
    point_area_threshold: float = 0.00047
    result_backend: str = "db+postgresql://smt:smt@localhost:5432"
    sam_checkpoint: str = "SMT-SAM"
    user_agent: str = "sketch-map-tool"
    weights_dir: str = str(get_project_root() / "weights")  # TODO: make this a Path
    wms_layers_esri_world_imagery: str = "world_imagery"
    wms_layers_esri_world_imagery_fallback: str = "world_imagery_fallback"
    wms_layers_osm: str = "heigit:osm-carto-proxy"
    wms_read_timeout: int = 600
    wms_url_esri_world_imagery: str = "https://maps.heigit.org/raster/sketch-map-tool/service?SERVICE=WMS&VERSION=1.1.1"
    wms_url_esri_world_imagery_fallback: str = "https://maps.heigit.org/raster/sketch-map-tool/service?SERVICE=WMS&VERSION=1.1.1"
    wms_url_osm: str = (
        "https://maps.heigit.org/raster/osm-carto/service?SERVICE=WMS&VERSION=1.1.1"
    )
    yolo_cls: str = "SMT-CLS"
    yolo_esri_obj: str = "SMT-ESRI"
    yolo_osm_obj: str = "SMT-OSM"

    model_config = SettingsConfigDict(
        env_prefix="SMT_",
        toml_file=get_config_path(),
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # https://docs.pydantic.dev/latest/concepts/pydantic_settings/#other-settings-source
        # env takes precedence over file settings
        return (env_settings, TomlConfigSettingsSource(settings_cls))

    @field_validator("esri_api_key", mode="before")
    @classmethod
    def check_esri_api_key(cls, value: str) -> str:
        if not value:
            logging.warning("No ESRI API Key found.")
        return value


CONFIG = Config()
