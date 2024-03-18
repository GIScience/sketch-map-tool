import pytest

from sketch_map_tool.helpers import get_project_root


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="session", autouse=True)
def configuration(monkeypatch_session):
    path = str(get_project_root() / "config" / "test.config.toml")
    yield monkeypatch_session.setenv("SMT_CONFIG", path)
