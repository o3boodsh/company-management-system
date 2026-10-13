"""Configuration guards, using only dictionaries and synthetic values."""

import socket

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.core.config import ConfigurationError, load_settings
from app.main import create_app


def local_config(**changes):
    return {"APP_ENV": "local", "AUTH_MODE": "development-stub", **changes}


@pytest.mark.parametrize("missing", ["APP_ENV", "AUTH_MODE"])
def test_required_settings_are_explicit(missing):
    config = local_config()
    del config[missing]
    with pytest.raises(ConfigurationError, match="Invalid or unsupported"):
        load_settings(config)


@pytest.mark.parametrize("env", ["", "invalid", "LOCAL", " prod "])
def test_invalid_environment_fails_safely(env):
    with pytest.raises(ConfigurationError) as failure:
        load_settings(local_config(APP_ENV=env))
    assert str(failure.value) == "Invalid or unsupported application configuration"


@pytest.mark.parametrize("env", ["local", "test"])
def test_local_and_test_start_without_database_configuration(env):
    settings = load_settings(local_config(APP_ENV=env))
    assert settings.database_url is None
    assert settings.dev_identity_role == "Viewer"


@pytest.mark.parametrize("env", ["staging", "production"])
def test_public_environment_rejects_development_stub(env):
    with pytest.raises(ConfigurationError):
        load_settings(local_config(APP_ENV=env))


@pytest.mark.parametrize("mode", ["", "invalid", "provider"])
def test_unavailable_authentication_never_falls_back(mode):
    with pytest.raises(ConfigurationError):
        load_settings(local_config(AUTH_MODE=mode))


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.0.2.1", "localhost"])
def test_stub_requires_an_explicit_loopback_ip(host):
    with pytest.raises(ConfigurationError):
        load_settings(local_config(API_BIND_HOST=host))


@pytest.mark.parametrize("field,value", [
    ("DEV_IDENTITY_ROLE", "Owner"),
    ("DATASET_CONTEXT", "approved-mvp"),
    ("EXPECTED_DATABASE_NAME", "company_db"),
    ("EXPECTED_DATABASE_NAME", "companyos_test"),
    ("SALARY_CURRENCY", "EUR"),
    ("SALARY_PERIOD", "yearly"),
    ("BUDGET_CURRENCY", "EUR"),
])
def test_unsafe_or_unapproved_settings_are_rejected(field, value):
    with pytest.raises(ConfigurationError):
        load_settings(local_config(**{field: value}))


@pytest.mark.parametrize("target", ["company_db", "companyos_test", "Company_DB", "%63ompany_db"])
@pytest.mark.parametrize("field", ["DATABASE_URL", "MIGRATION_DATABASE_URL", "TEST_DATABASE_URL"])
def test_training_and_unapproved_test_targets_are_forbidden(field, target):
    with pytest.raises(ConfigurationError):
        load_settings(local_config(**{field: f"mysql+pymysql://example.invalid/{target}"}))


def test_approved_dev_dsn_is_checked_without_access_and_masked(monkeypatch):
    def reject_connection(*args, **kwargs):
        raise AssertionError("Settings must not connect")

    monkeypatch.setattr(socket, "create_connection", reject_connection)
    settings = load_settings(local_config(DATABASE_URL="mysql+pymysql://example.invalid/companyos_dev"))
    assert settings.expected_database_name == "companyos_dev"
    assert "example.invalid" not in repr(settings)


@pytest.mark.parametrize("field", ["DATABASE_URL", "MIGRATION_DATABASE_URL", "TEST_DATABASE_URL"])
def test_test_mode_cannot_use_even_the_development_database(field):
    with pytest.raises(ConfigurationError):
        load_settings(local_config(APP_ENV="test", **{field: "mysql://example.invalid/companyos_dev"}))


def test_configuration_error_does_not_expose_secret_or_input():
    private_value = "synthetic-redaction-marker"
    with pytest.raises(ConfigurationError) as failure:
        load_settings(local_config(DATABASE_URL=private_value))
    assert private_value not in str(failure.value)
    assert private_value not in repr(failure.value)
    assert failure.value.__suppress_context__


def test_missing_environment_blocks_application_startup(monkeypatch):
    monkeypatch.delenv("APP_ENV")
    with pytest.raises(ConfigurationError):
        with TestClient(create_app()):
            pytest.fail("Startup must fail closed")


@pytest.mark.parametrize("dsn", [
    "mysql+pymysql://example.invalid/companyos_\tdev",
    "mysql+pymysql://example.invalid/companyos_\ndev",
    "mysql+pymysql://example.invalid/companyos_\rdev",
    "mysql+pymysql://example.invalid/companyos_dev\x00",
    "mysql+pymysql://example.invalid/companyos_dev\x7f",
    "mysql+pymysql://example.invalid/companyos_dev#",
    "mysql+pymysql://example.invalid/companyos_dev#fragment",
    " mysql+pymysql://example.invalid/companyos_dev",
    "mysql+pymysql://example.invalid/companyos_dev ",
    "mysql+pymysql://example.invalid/companyos_ dev",
    "mysql+pymysql://example.invalid/companyos_dev?",
    "mysql+pymysql://example.invalid/companyos_dev?charset=utf8mb4",
    "mysql+pymysql://example.invalid/companyos%0adev",
    "mysql+pymysql://synthetic%09user@example.invalid/companyos_dev",
    "mysql+pymysql://synthetic-user:synthetic%0apassword@example.invalid/companyos_dev",
    "mysql+pymysql://example.invalid/companyos%255fdev",
    "mysql+pymysql://example.invalid/company_db",
    "mysql+pymysql://example.invalid/companyos_test",
    "mysql+pymysql://example.invalid/companyos_dev/../company_db",
    "mysql+pymysql://example.invalid/Companyos_dev",
    "mysql+pymysql://example.invalid",
    "mysql+pymysql:///companyos_dev",
    "mysql+pymysql://example.invalid:not-a-port/companyos_dev",
    "mysql+pymysql://example.invalid:0/companyos_dev",
    "mysql+pymysql://example.invalid:65536/companyos_dev",
    "mysql+pymysql://[broken/companyos_dev",
    "mysql+pymysql://[not-an-ip]/companyos_dev",
    "mysql+pymysql://example.invalid\\other/companyos_dev",
    "mysql+pymysql://example%0ainvalid/companyos_dev",
    "postgresql://example.invalid/companyos_dev",
    "not-a-url",
])
@pytest.mark.parametrize("field", ["DATABASE_URL", "MIGRATION_DATABASE_URL"])
def test_dsn_edge_cases_are_rejected_safely(field, dsn):
    with pytest.raises(ConfigurationError) as failure:
        load_settings(local_config(**{field: dsn}))
    assert str(failure.value) == "Invalid or unsupported application configuration"
    assert dsn not in str(failure.value)
    assert "synthetic" not in str(failure.value)


@pytest.mark.parametrize("dsn", [
    "mysql+pymysql://example.invalid/companyos_dev",
    "mysql+pymysql://example.invalid/companyos%5fdev",
    "mysql+pymysql://synthetic%40user:synthetic%23%3F%2F%40password@example.invalid:3306/companyos_dev",
    "mysql+pymysql://[::1]:3306/companyos_dev",
])
def test_accepted_dsn_matches_the_exact_driver_database(dsn):
    settings = load_settings(local_config(DATABASE_URL=dsn))
    parsed = make_url(settings.database_url.get_secret_value())
    assert parsed.database == settings.expected_database_name
    assert dsn not in repr(settings)
    for credential in (parsed.username, parsed.password):
        if credential:
            assert credential not in repr(settings)


def test_malformed_dsn_with_credentials_never_leaks_them(caplog):
    dsn = "mysql+pymysql://synthetic-user:synthetic-password@example.invalid:bad-port/companyos_dev"
    with pytest.raises(ConfigurationError) as failure:
        load_settings(local_config(DATABASE_URL=dsn))
    output = str(failure.value) + repr(failure.value) + caplog.text
    assert "synthetic-password" not in output
    assert dsn not in output
