from io import BytesIO
from unittest.mock import Mock

import pytest
from celery.result import GroupResult


@pytest.mark.usefixtures("mock_async_result_success")
def test_download_success(client, uuid):
    resp = client.get("/api/download/{0}/sketch-map".format(uuid))
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"


@pytest.mark.usefixtures("mock_async_result_started")
def test_download_started(client, uuid):
    resp = client.get("/api/download/{0}/sketch-map".format(uuid))
    assert resp.status_code == 500


@pytest.mark.usefixtures("mock_async_result_failure")
def test_download_failure(client, uuid):
    resp = client.get("/api/download/{0}/sketch-map".format(uuid))
    assert resp.status_code == 500


@pytest.mark.usefixtures("mock_group_result_success")
@pytest.mark.parametrize("type_", ["raster-results", "vector-results"])
def test_group_download_success(client, uuid, type_, monkeypatch):
    monkeypatch.setattr(
        "sketch_map_tool.routes.merge",
        lambda *_: {"type": "FeatureCollection", "features": []},
    )
    monkeypatch.setattr(
        "sketch_map_tool.routes.zip_",
        lambda *_: BytesIO(),
    )
    resp = client.get("/api/download/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype in ["application/zip", "application/geo+json"]


@pytest.mark.usefixtures("mock_group_result_started")
@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_started(client, uuid, type_):
    resp = client.get("/api/download/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500


@pytest.mark.usefixtures("mock_group_result_failure")
@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_failure(client, uuid, type_):
    resp = client.get("/api/download/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500


@pytest.mark.usefixtures("mock_group_result_started_success_failure")
@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_started_success_failure(client, uuid, type_):
    resp = client.get("/api/download/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_success_failure(
    client,
    uuid,
    type_,
    mock_async_result_success,
    mock_async_result_failure,
    monkeypatch,
):
    monkeypatch.setattr(
        "sketch_map_tool.routes.merge",
        lambda *_: {"type": "FeatureCollection", "features": []},
    )
    monkeypatch.setattr(
        "sketch_map_tool.routes.zip_",
        lambda *_: BytesIO(),
    )

    mock = Mock(spec=GroupResult)
    mock.ready.return_value = True
    mock.failed.return_value = True
    mock.successful.return_value = False
    mock.results = [
        mock_async_result_success,
        mock_async_result_failure,
    ]
    mock.get.return_value = [[mock_async_result_success.get]]
    monkeypatch.setattr("sketch_map_tool.routes.get_async_result", lambda *_: mock)

    resp = client.get("/api/download/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype in ["application/zip", "application/geo+json"]
