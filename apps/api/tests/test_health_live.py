"""Liveness contract checks using in-process HTTP requests."""

import socket
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_health_live_returns_exact_response():
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}
    assert response.headers["content-type"] == "application/json"


@pytest.mark.parametrize(
    "query",
    ["?q=private-value", "?q=first&q=second", "?unexpected=", "?private-name=private-value"],
)
def test_health_live_rejects_query_without_echoing_input(query):
    with TestClient(app) as client:
        response = client.get(f"/api/v1/health/live{query}")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["message"] == "Request validation failed"
    assert error["details"] == [
        {
            "field": "query",
            "code": "unsupported_query_parameter",
            "message": "Query parameters are not supported",
        }
    ]
    assert UUID(error["request_id"]).version == 4
    for private_input in ("private-value", "private-name", "first", "second", "unexpected"):
        assert private_input not in response.text


def test_openapi_describes_liveness_and_only_that_application_path():
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert set(schema["paths"]) == {"/api/v1/health/live"}
    operation = schema["paths"]["/api/v1/health/live"]["get"]
    assert "200" in operation["responses"]
    assert "422" in operation["responses"]
    assert "parameters" not in operation
    response_model = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert response_model["$ref"] == "#/components/schemas/LivenessResponse"


def test_swagger_ui_is_available():
    with TestClient(app) as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SwaggerUIBundle" in response.text
    assert "/openapi.json" in response.text


def test_startup_and_liveness_need_no_database_settings_or_outbound_connection(monkeypatch):
    for name in ("DATABASE_URL", "MIGRATION_DATABASE_URL", "TEST_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)

    def reject_network_connection(*args, **kwargs):
        raise AssertionError("Liveness must not open a network connection")

    # Windows asyncio uses a local socketpair internally; do not block that.
    monkeypatch.setattr(socket, "create_connection", reject_network_connection)
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").json() == {"data": {"status": "ok"}}
