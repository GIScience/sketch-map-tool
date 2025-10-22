from pathlib import Path

import pytest
from vcr.stubs import VCRHTTPResponse


@pytest.fixture(scope="session")
def monkeypatch_session():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


# HACK: temporary workaround of https://github.com/kevin1024/vcrpy/issues/888
@pytest.fixture(scope="session", autouse=True)
def patch_vcrhttpresponse_version_string():
    if not hasattr(VCRHTTPResponse, "version_string"):
        VCRHTTPResponse.version_string = None
    yield


@pytest.fixture(autouse=True)
def config_for_test(monkeypatch):
    # NOTE: Config file is empty. Default values will be used.
    path = Path(__file__).parent.parent.resolve() / "config" / "test.config.toml"
    monkeypatch.setenv("SMT_CONFIG", str(path))
