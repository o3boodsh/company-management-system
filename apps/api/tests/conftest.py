"""Give every test synthetic configuration independent of the operator's secrets."""

import pytest
import socket
import sqlalchemy
from sqlalchemy.engine import Engine

from app.core.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    for field in Settings.model_fields.values():
        monkeypatch.delenv(field.alias, raising=False)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AUTH_MODE", "development-stub")


@pytest.fixture(autouse=True)
def forbid_database_access(monkeypatch):
    """All tests stay in-process with fake sessions and no engine/DB connection."""
    def forbidden(*args, **kwargs):
        raise AssertionError("Engine construction and database connections are forbidden in these tests")

    monkeypatch.setattr(sqlalchemy, "create_engine", forbidden)
    monkeypatch.setattr(sqlalchemy.engine, "create_engine", forbidden)
    monkeypatch.setattr(sqlalchemy.engine.create, "create_engine", forbidden)
    monkeypatch.setattr(Engine, "connect", forbidden)
    monkeypatch.setattr(Engine, "raw_connection", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
