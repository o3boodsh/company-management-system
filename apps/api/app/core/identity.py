"""Prepare a trusted local principal; no provider or public login implementation."""

from ipaddress import ip_address
from typing import Literal

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings


class Principal(BaseModel):
    model_config = ConfigDict(frozen=True)
    subject: Literal["synthetic-development-user"] = "synthetic-development-user"
    role: Literal["Administrator", "Viewer"]


def get_development_principal(request: Request) -> Principal:
    """Future dependency: trust server settings and ASGI addresses, never headers."""
    settings: Settings | None = getattr(request.app.state, "settings", None)
    server = request.scope.get("server")
    client = request.scope.get("client")
    try:
        loopback = bool(
            server and client
            and ip_address(server[0]).is_loopback
            and ip_address(client[0]).is_loopback
        )
    except ValueError:
        loopback = False
    if (
        settings is None
        or settings.app_env not in ("local", "test")
        or settings.auth_mode != "development-stub"
        or settings.dataset_context != "synthetic-mvp"
        or not loopback
    ):
        raise HTTPException(status_code=401)
    return Principal(role=settings.dev_identity_role)
