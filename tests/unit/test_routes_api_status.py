import pytest


def test_status_success(
    client,
    uuid,
    mock_async_result_success,
):
    resp = client.get("/api/status/{0}/sketch-map".format(uuid))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == "/api/download/{0}/sketch-map".format(uuid)
    assert "info" not in resp.json.keys()
    assert "errors" not in resp.json.keys()


def test_status_started(
    client,
    uuid,
    mock_async_result_started,
):
    resp = client.get("/api/status/{0}/sketch-map".format(uuid))
    assert resp.status_code == 202
    assert resp.json["id"] == uuid
    assert resp.json["type"] == "sketch-map"
    assert resp.json["status"] == "STARTED"
    assert resp.json["info"] == {"current": 0, "total": 1}
    assert "href" not in resp.json.keys()
    assert "errors" not in resp.json.keys()


def test_status_failure(
    client,
    uuid,
    mock_async_result_failure,
):
    resp = client.get("/api/status/{0}/sketch-map".format(uuid))
    assert resp.status_code == 422
    assert resp.json["id"] == uuid
    assert resp.json["type"] == "sketch-map"
    assert resp.json["status"] == "FAILURE"
    assert resp.json["errors"] == ["QRCodeError: Mock error"]
    assert "href" not in resp.json.keys()


def test_status_failure_hard(
    client,
    uuid,
    mock_async_result_failure_hard,
):
    resp = client.get("/api/status/{0}/sketch-map".format(uuid))
    assert resp.status_code == 500


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_success(
    client,
    uuid,
    type_,
    mock_group_result_success,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_started(
    client,
    uuid,
    type_,
    mock_group_result_started,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "STARTED"
    assert resp.json["info"] == {"current": 0, "total": 1}


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_failure(
    client,
    uuid,
    type_,
    mock_group_result_failure,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 422
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "FAILURE"
    assert resp.json["errors"] == ["QRCodeError: Mock error"]


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_failure_hard(
    client,
    uuid,
    type_,
    mock_group_result_failure_hard,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_started_success_failure(
    client,
    uuid,
    type_,
    mock_group_result_started_success_failure,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 202
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "STARTED"
    assert resp.json["errors"] == ["QRCodeError: Mock error"]
    assert resp.json["info"] == {"current": 2, "total": 3}


@pytest.mark.parametrize("type_", ("raster-results", "vector-results"))
def test_group_status_success_failure(
    client,
    uuid,
    type_,
    mock_group_result_success_failure,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["errors"] == ["QRCodeError: Mock error"]
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)
    assert "info" not in resp.json.keys()
