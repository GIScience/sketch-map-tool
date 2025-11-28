import os
from pathlib import Path

import pytest
import pytest_approval
from pytest_approval.config import tomllib

from sketch_map_tool import config, definitions
from tests import vcr_app as vcr


@pytest.fixture(params=["osm", "oam:59e62beb3d6412ef7220c58e"])
def layer(request):
    return request.param


def test_get_literatur_references():
    result = definitions.get_literature_references()
    for r in result:
        assert r.img_src is not None
        assert r.citation is not None


@vcr.use_cassette
def test_get_attribution_esri_api_key_unset(monkeypatch):
    monkeypatch.setattr("sketch_map_tool.definitions.CONFIG.esri_api_key", "")
    assert pytest_approval.verify(definitions.get_attribution("esri-world-imagery"))


@vcr.use_cassette
@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Detected CI environment. ESRI API Key not set in CI.",
)
def test_get_attribution_esri_api_key_set(monkeypatch):
    path = Path(__file__).parent.parent.parent.resolve() / "config" / "config.toml"
    with open(path, "rb") as f:
        conf = tomllib.load(f)
    monkeypatch.setenv("SMT_ESRI_API_KEY", conf["esri_api_key"])
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/#in-place-reloading
    config.CONFIG.__init__()

    assert pytest_approval.verify(definitions.get_attribution("esri-world-imagery"))


@vcr.use_cassette
def test_get_attribution(layer):
    assert pytest_approval.verify(definitions.get_attribution(layer))


def test_get_attribution_no_esri_esri_api_key(monkeypatch):
    monkeypatch.setattr("sketch_map_tool.definitions.CONFIG.esri_api_key", "")
    result = definitions.get_attribution("esri-world-imagery")
    assert result == (
        "Powered by Esri<br />Esri, Maxar, Earthstar Geographics, and the GIS User "
        + "Community"
    )
