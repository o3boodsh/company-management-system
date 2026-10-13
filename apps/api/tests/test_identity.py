"""Test a future dependency with test-only routes; ship no identity endpoint."""

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from uvicorn import Config

from app.core.config import load_settings
from app.core.identity import Principal, get_development_principal
from app.main import create_app


def identity_test_app(role="Viewer"):
    application = create_app(load_settings({
        "APP_ENV": "test", "AUTH_MODE": "development-stub", "DEV_IDENTITY_ROLE": role,
    }))

    @application.get("/_test/principal")
    def principal(identity: Principal = Depends(get_development_principal)):
        return {"role": identity.role, "subject": identity.subject}

    return application


@pytest.mark.parametrize("configured,claimed", [("Viewer", "Administrator"), ("Administrator", "Viewer")])
def test_browser_headers_cannot_override_trusted_role(configured, claimed):
    with TestClient(identity_test_app(configured), base_url="http://127.0.0.1", client=("127.0.0.1", 1234)) as client:
        response = client.get("/_test/principal", headers={
            "X-Role": claimed, "X-User-Role": claimed, "Authorization": "Bearer synthetic-value",
        })
    assert response.status_code == 200
    assert response.json() == {"role": configured, "subject": "synthetic-development-user"}


@pytest.mark.parametrize("server,client_address", [
    ("http://192.0.2.1", ("127.0.0.1", 1234)),
    ("http://127.0.0.1", ("192.0.2.1", 1234)),
])
def test_host_and_forwarded_headers_do_not_enable_remote_stub(server, client_address):
    with TestClient(identity_test_app(), base_url=server, client=client_address) as client:
        response = client.get("/_test/principal", headers={
            "Host": "localhost", "X-Forwarded-For": "127.0.0.1", "X-Role": "Administrator",
        })
    assert response.status_code == 401
    assert response.json()["error"]["details"] == []


def test_missing_trusted_settings_never_authenticates():
    with TestClient(identity_test_app(), base_url="http://127.0.0.1", client=("127.0.0.1", 1234)) as client:
        client.app.state.settings = None
        response = client.get("/_test/principal")
    assert response.status_code == 401


def test_shipped_application_has_no_identity_or_business_endpoint():
    assert set(create_app().openapi()["paths"]) == {"/api/v1/health/live"}


@pytest.mark.parametrize("address,expected", [("192.0.2.1", 401), ("127.0.0.1", 200)])
def test_uvicorn_without_proxy_headers_preserves_real_client_boundary(address, expected):
    # Load Uvicorn's ASGI wrapper only; no external server/socket is started.
    config = Config(identity_test_app(), host="127.0.0.1", proxy_headers=False, log_config=None)
    config.load()
    with TestClient(config.loaded_app, base_url="http://127.0.0.1", client=(address, 1234)) as client:
        response = client.get("/_test/principal", headers={
            "X-Forwarded-For": "127.0.0.1",
            "X-Forwarded-Proto": "https",
            "X-Role": "Administrator",
        })
    assert response.status_code == expected
    if expected == 200:
        assert response.json()["role"] == "Viewer"
