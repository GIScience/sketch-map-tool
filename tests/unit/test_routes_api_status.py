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


@pytest.mark.parametrize(
    "lang",
    [
        ("", "QRCodeError: QR-Code could not be detected."),
        ("/de", "QRCodeError: QR-Code konnte nicht erkannt werden."),
        ("/en", "QRCodeError: QR-Code could not be detected."),
    ],
)
def test_status_failure(
    client,
    uuid,
    mock_async_result_failure,
    lang,
):
    resp = client.get("{0}/api/status/{1}/sketch-map".format(lang[0], uuid))
    assert resp.status_code == 422
    assert resp.json["id"] == uuid
    assert resp.json["type"] == "sketch-map"
    assert resp.json["status"] == "FAILURE"
    assert resp.json["errors"] == [lang[1]]
    assert "href" not in resp.json.keys()


def test_status_failure_time_limit_exceeded(
    client,
    uuid,
    mock_async_result_failure_time_limit_exceeded,
):
    """Billiard/Celery exception should be wrapped for the user"""
    resp = client.get("/api/status/{0}/sketch-map".format(uuid))
    assert resp.status_code == 422
    assert resp.json["id"] == uuid
    assert resp.json["type"] == "sketch-map"
    assert resp.json["status"] == "FAILURE"
    assert resp.json["errors"] == [
        (
            "TimeLimitExceededError: We couldn’t process your submission because it "
            "took too long. Please try again later. If the problem persists, reach out "
            "to us: sketch-map-tool@heigit.org"
        )
    ]
    assert "href" not in resp.json.keys()


def test_status_failure_hard(
    client,
    uuid,
    mock_async_result_failure_hard,
):
    resp = client.get("/api/status/{0}/sketch-map".format(uuid))
    assert resp.status_code == 500
    assert "Internal Server Error" in resp.text
    assert "Oops... we seem to have made a mistake, sorry!" in resp.text


@pytest.mark.parametrize(
    "type_",
    (
        "raster-results",
        "vector-results",
        "centroid-results",
    ),
)
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


@pytest.mark.parametrize(
    "type_",
    (
        "raster-results",
        "vector-results",
        "centroid-results",
    ),
)
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


@pytest.mark.parametrize(
    "type_",
    (
        "raster-results",
        "vector-results",
        "centroid-results",
    ),
)
@pytest.mark.parametrize(
    "lang",
    [
        ("", "QRCodeError: QR-Code could not be detected."),
        ("/de", "QRCodeError: QR-Code konnte nicht erkannt werden."),
        ("/en", "QRCodeError: QR-Code could not be detected."),
    ],
)
def test_group_status_failure(client, uuid, type_, mock_group_result_failure, lang):
    resp = client.get("{0}/api/status/{1}/{2}".format(lang[0], uuid, type_))
    assert resp.status_code == 422
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "FAILURE"
    assert resp.json["errors"] == [lang[1]]


@pytest.mark.parametrize(
    "type_",
    (
        "raster-results",
        "vector-results",
        "centroid-results",
    ),
)
def test_group_status_failure_hard(
    client,
    uuid,
    type_,
    mock_group_result_failure_hard,
):
    resp = client.get("/api/status/{0}/{1}".format(uuid, type_))
    assert resp.status_code == 500


@pytest.mark.parametrize(
    "lang",
    [
        ("", "QRCodeError: QR-Code could not be detected."),
        ("/de", "QRCodeError: QR-Code konnte nicht erkannt werden."),
        ("/en", "QRCodeError: QR-Code could not be detected."),
    ],
)
@pytest.mark.parametrize(
    "type_",
    (
        "raster-results",
        "vector-results",
        "centroid-results",
    ),
)
def test_group_status_started_success_failure(
    client,
    uuid,
    type_,
    mock_group_result_started_success_failure,
    lang,
):
    resp = client.get("{0}/api/status/{1}/{2}".format(lang[0], uuid, type_))
    assert resp.status_code == 202
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "STARTED"
    assert resp.json["errors"] == [lang[1]]
    assert resp.json["info"] == {"current": 2, "total": 3}


@pytest.mark.parametrize(
    "lang",
    [
        ("", "QRCodeError: QR-Code could not be detected."),
        ("/de", "QRCodeError: QR-Code konnte nicht erkannt werden."),
        ("/en", "QRCodeError: QR-Code could not be detected."),
    ],
)
@pytest.mark.parametrize(
    "type_",
    (
        "raster-results",
        "vector-results",
        "centroid-results",
    ),
)
def test_group_status_success_failure(
    client, uuid, type_, mock_group_result_success_failure, lang
):
    resp = client.get("{0}/api/status/{1}/{2}".format(lang[0], uuid, type_))
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    assert resp.json["id"] == uuid
    assert resp.json["type"] == type_
    assert resp.json["status"] == "SUCCESS"
    assert resp.json["errors"] == [lang[1]]
    assert resp.json["href"] == "/api/download/{0}/{1}".format(uuid, type_)
    assert "info" not in resp.json.keys()
