"""Response/log redaction and request-ID consistency using synthetic failures."""

from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import create_app


def test_request_ids_are_generated_not_trusted_from_browser():
    with TestClient(create_app()) as client:
        first = client.get("/api/v1/health/live", headers={"X-Request-ID": "browser-controlled"})
        second = client.get("/api/v1/health/live")
    assert UUID(first.headers["X-Request-ID"]).version == 4
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
    assert first.headers["Cache-Control"] == "private, no-store"


def test_validation_handler_does_not_serialize_raw_input():
    application = create_app()

    @application.get("/_test/validation")
    def validation(secret: int):
        return {"value": secret}

    with TestClient(application) as client:
        response = client.get("/_test/validation?secret=synthetic-redaction-marker")
    assert response.status_code == 422
    assert response.json()["error"]["details"] == []
    assert "synthetic-redaction-marker" not in response.text
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_unexpected_errors_never_log_or_return_exception_secrets(caplog):
    application = create_app()

    @application.get("/_test/failure")
    def failure():
        raise RuntimeError("synthetic-secret-in-exception")

    with TestClient(application) as client:
        response = client.get("/_test/failure")
    assert response.status_code == 500
    error = response.json()["error"]
    assert error == {"code": "internal_error", "message": "Unexpected server error", "details": [],
                     "request_id": response.headers["X-Request-ID"]}
    assert "synthetic-secret-in-exception" not in response.text + caplog.text
    records = [record for record in caplog.records if record.name == "companyos.requests"]
    assert len(records) == 1
    assert records[0].exc_info is None
    assert error["request_id"] in records[0].getMessage()


def test_http_exception_detail_is_also_redacted():
    application = create_app()

    @application.get("/_test/http-error")
    def failure():
        raise HTTPException(status_code=403, detail="synthetic-sensitive-detail")

    with TestClient(application) as client:
        response = client.get("/_test/http-error")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert "synthetic-sensitive-detail" not in response.text


@pytest.mark.parametrize("method,path,status", [
    ("get", "/missing", 404), ("post", "/api/v1/health/live", 405),
])
def test_framework_errors_use_safe_envelope(method, path, status):
    with TestClient(create_app()) as client:
        response = getattr(client, method)(path)
    assert response.status_code == status
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    if status == 405:
        assert "GET" in response.headers["Allow"]
