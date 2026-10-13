"""Read only recognized environment variables; never connect or load .env files."""

import os
from collections.abc import Mapping
from ipaddress import ip_address
from typing import Literal

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, model_validator
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class ConfigurationError(RuntimeError):
    """Safe startup failure without raw settings or chained validation errors."""


class Settings(BaseModel):
    model_config = ConfigDict(
        alias_generator=str.upper,
        populate_by_name=True,
        extra="forbid",
        strict=True,
        frozen=True,
        hide_input_in_errors=True,
    )

    app_env: Literal["local", "test", "staging", "production"]
    auth_mode: Literal["development-stub", "provider"]
    api_bind_host: str = "127.0.0.1"
    dev_identity_role: Literal["Administrator", "Viewer"] = "Viewer"
    dataset_context: Literal["synthetic-mvp", "approved-mvp"] = "synthetic-mvp"
    expected_database_name: Literal["companyos_dev"] = "companyos_dev"
    database_url: SecretStr | None = None
    migration_database_url: SecretStr | None = None
    test_database_url: SecretStr | None = None
    salary_currency: Literal["USD"] = "USD"
    salary_period: Literal["monthly"] = "monthly"
    budget_currency: Literal["USD"] = "USD"

    @model_validator(mode="after")
    def validate_boundaries(self) -> "Settings":
        if self.auth_mode == "provider":
            raise ValueError("Provider authentication is not implemented")
        if self.app_env not in ("local", "test"):
            raise ValueError("Development identity is forbidden in public environments")
        if self.dataset_context != "synthetic-mvp":
            raise ValueError("Development identity requires synthetic data")
        try:
            loopback = ip_address(self.api_bind_host).is_loopback
        except ValueError:
            loopback = False
        if not loopback:
            raise ValueError("Development identity requires an explicit loopback IP")

        for secret in (self.database_url, self.migration_database_url, self.test_database_url):
            if secret is None or not secret.get_secret_value():
                continue
            if self.app_env == "test" or secret is self.test_database_url:
                raise ValueError("Database use by tests is not approved")
            try:
                raw_url = secret.get_secret_value()
                # URL parsing must not silently normalize controls/whitespace.
                if any(char.isspace() or ord(char) < 32 or 127 <= ord(char) <= 159 for char in raw_url):
                    raise ValueError("Invalid database URL")
                # Query options remain unsupported; reserved password characters
                # must be percent-encoded rather than interpreted ambiguously.
                if "#" in raw_url or "?" in raw_url:
                    raise ValueError("Invalid database URL")
                parsed = make_url(raw_url)
                components = (parsed.username, parsed.password, parsed.host, parsed.database)
                if any(
                    ord(char) < 32 or 127 <= ord(char) <= 159
                    for component in components if component is not None
                    for char in component
                ):
                    raise ValueError("Invalid database URL")
                host = parsed.host or ""
                if any(char in host for char in "[]/\\@%"):
                    raise ValueError("Invalid database URL")
                if ":" in host or f"[{host}]" in raw_url:
                    if ip_address(host).version != 6:
                        raise ValueError("Invalid database URL")
                valid = (
                    parsed.drivername in ("mysql", "mysql+pymysql")
                    and bool(host)
                    and not any(char.isspace() for char in host)
                    and parsed.database == self.expected_database_name
                    and not parsed.query
                    and (parsed.port is None or 1 <= parsed.port <= 65535)
                )
            except (ArgumentError, ValueError):
                valid = False
            if not valid:
                raise ValueError("Database target must be the approved isolated development target")
        return self


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Validate process configuration without logging values or using credentials."""
    source = os.environ if environ is None else environ
    values = {
        field.alias: source[field.alias]
        for field in Settings.model_fields.values()
        if field.alias in source
    }
    try:
        return Settings.model_validate(values)
    except (ValidationError, ValueError):
        raise ConfigurationError("Invalid or unsupported application configuration") from None
