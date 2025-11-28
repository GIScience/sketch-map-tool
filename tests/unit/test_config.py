import logging
import os

from sketch_map_tool import config


def test_config():
    # SMT_CONFIG environment variable is set in pyproject.toml for pytest test runs
    assert config.Config().model_config["toml_file"] == "config/test.config.toml"


def test_default_data_dir():
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
    assert config.CONFIG.data_dir == expected


def test_esri_key(caplog):
    with caplog.at_level(logging.WARNING):
        assert config.Config().esri_api_key == ""
        assert "No ESRI API Key found." in caplog.text


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


def test_config_user_agent_env(monkeypatch):
    # env takes precedence over file (see pyproject.toml)
    assert config.CONFIG.user_agent == "sketch-map-tool-test"


def test_config_user_agent_file(monkeypatch):
    monkeypatch.delenv("SMT_USER_AGENT", raising=False)
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/#in-place-reloading
    config.CONFIG.__init__()
    assert config.CONFIG.user_agent == "foo"
