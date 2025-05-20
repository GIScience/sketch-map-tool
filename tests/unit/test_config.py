import os
from unittest import mock

import pytest

from sketch_map_tool import config


@pytest.fixture
def mock_env_user(monkeypatch):
    monkeypatch.setenv("USER", "TestingUser")


@pytest.fixture
def mock_env_missing(monkeypatch):
    monkeypatch.delenv("USER", raising=False)


@pytest.fixture
def config_keys():
    return (
        "data-dir",
        "weights-dir",
        "user-agent",
        "broker-url",
        "result-backend",
        "cleanup-map-frames-interval",
        "wms-url-osm",
        "wms-layers-osm",
        "wms-url-esri-world-imagery",
        "wms-url-esri-world-imagery-fallback",
        "wms-layers-esri-world-imagery",
        "wms-layers-esri-world-imagery-fallback",
        "wms-read-timeout",
        "max-nr-simultaneous-uploads",
        "yolo_cls",
        "yolo_osm_obj",
        "yolo_esri_obj",
        "model_type_sam",
        "esri-api-key",
        "log-level",
    )


def test_get_config_path_empty_env(monkeypatch):
    monkeypatch.delenv("SMT_CONFIG", raising=False)
    assert config.get_config_path() == os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "config",
            "config.toml",
        )
    )


def test_get_config_path_set_env(monkeypatch):
    monkeypatch.setenv("SMT_CONFIG", "/some/absolute/path")
    assert config.get_config_path() == "/some/absolute/path"


def test_config_default(monkeypatch, config_keys):
    monkeypatch.delenv("SMT_CONFIG", raising=False)
    assert tuple(config.DEFAULT_CONFIG.keys()) == config_keys


def test_load_config_from_file(monkeypatch):
    monkeypatch.setenv(
        "SMT_CONFIG",
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures", "config.toml"
        ),
    )
    path = config.get_config_path()
    cfg = config.load_config_from_file(path)
    expected = {"data-dir": "/some/absolute/path", "user-agent": "sketch-map-tool"}
    assert cfg == expected


@mock.patch.dict("os.environ", {}, clear=True)
def test_get_config(config_keys):
    cfg = config.get_config()
    assert tuple(cfg.keys()) == config_keys


@mock.patch.dict("os.environ", {}, clear=True)
def test_get_config_value(config_keys):
    for key in config_keys:
        val = config.get_config_value(key)
        if key in [
            "wms-read-timeout",
            "max-nr-simultaneous-uploads",
            "max_pixel_per_image",
        ]:
            assert isinstance(val, int | float)
        else:
            assert isinstance(val, str)


@mock.patch.dict(
    "os.environ",
    {"SMT_CONFIG": ""},
    clear=True,
)
def test_get_config_env_empty_str(config_keys):
    cfg = config.get_config()
    assert tuple(cfg.keys()) == config_keys


def test_data_dir():
    expected = os.path.abspath(
        os.path.join(
            os.path.dirname(
                os.path.abspath(__file__),
            ),
            "..",
            "..",
            "data",
        )
    )
    assert config.DEFAULT_CONFIG["data-dir"] == expected
