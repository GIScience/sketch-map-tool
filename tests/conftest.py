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
