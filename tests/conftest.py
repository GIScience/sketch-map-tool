import pytest
from vcr.stubs import VCRHTTPResponse

from sketch_map_tool.helpers import get_project_root


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="session", autouse=True)
def configuration(monkeypatch_session):
    path = str(get_project_root() / "config" / "test.config.toml")
    yield monkeypatch_session.setenv("SMT_CONFIG", path)


# HACK: temporary workaround of https://github.com/kevin1024/vcrpy/issues/888
@pytest.fixture(scope="session", autouse=True)
def patch_vcrhttpresponse_version_string():
    if not hasattr(VCRHTTPResponse, "version_string"):
        VCRHTTPResponse.version_string = None
    yield
