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
        "user-agent",
        "broker-url",
        "result-backend",
        "data-store",
        "wms-url",
        "wms-layers",
    )


def test_get_config_path_empty_env(monkeypatch):
    monkeypatch.delenv("SMT-CONFIG", raising=False)
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
    monkeypatch.setenv("SMT-CONFIG", "/some/absolute/path")
    assert config.get_config_path() == "/some/absolute/path"


def test_config_default(monkeypatch, config_keys):
    monkeypatch.delenv("SMT-CONFIG", raising=False)
    cfg = config.load_config_default()
    assert tuple(cfg.keys()) == config_keys


def test_load_config_from_file(monkeypatch):
    monkeypatch.setenv(
        "SMT-CONFIG",
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures", "config.toml"
        ),
    )
    path = config.get_config_path()
    cfg = config.load_config_from_file(path)
    expected = {"data-dir": "/some/absolute/path", "user-agent": "sketch-map-tool"}
    assert cfg == expected


@mock.patch.dict("os.environ", {}, clear=True)
def test_load_config_from_env_empty():
    cfg = config.load_config_from_env()
    assert cfg == {}


@mock.patch.dict(
    "os.environ",
    {"SMT-DATA-DIR": "foo", "SMT-USER-AGENT": "bar"},
    clear=True,
)
def test_load_config_from_env_set():
    cfg = config.load_config_from_env()
    assert cfg == {"data-dir": "foo", "user-agent": "bar"}


@mock.patch.dict("os.environ", {}, clear=True)
def test_get_config(config_keys):
    cfg = config.get_config()
    assert tuple(cfg.keys()) == config_keys


@mock.patch.dict("os.environ", {}, clear=True)
def test_get_config_value(config_keys):
    for key in config_keys:
        val = config.get_config_value(key)
        assert isinstance(val, str)


@mock.patch.dict(
    "os.environ",
    {"SMT-CONFIG": ""},
    clear=True,
)
def test_get_config_env_empty_str(config_keys):
    cfg = config.get_config()
    assert tuple(cfg.keys()) == config_keys


@mock.patch.dict("os.environ", {}, clear=True)
def test_get_data_dir_unset_env(config_keys):
    data_dir = config.get_default_data_dir()
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
    assert data_dir == expected
