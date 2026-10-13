"""Online-path tests use synthetic credentials and fake engines only."""

from contextlib import contextmanager

import pytest
import sqlalchemy

from app.db.migration import migration_url, run_online


def synthetic_settings():
    # Construct fixture URL in memory; no real credential is read.
    url = sqlalchemy.URL.create(
        "mysql+pymysql", username="companyos_migrator", password="synthetic-only",
        host="127.0.0.1", port=3306, database="companyos_dev",
    )
    return {"APP_ENV": "local", "AUTH_MODE": "development-stub",
            "MIGRATION_OPERATION_OPT_IN": "approved",
            "MIGRATION_DATABASE_URL": url.render_as_string(hide_password=False)}


def test_approved_settings_parse_without_engine():
    url = migration_url(synthetic_settings())
    assert (url.host, url.port, url.database, url.username) == (
        "127.0.0.1", 3306, "companyos_dev", "companyos_migrator",
    )


@pytest.mark.parametrize("key,value", [
    ("APP_ENV", "test"), ("APP_ENV", "production"), ("APP_ENV", ""),
    ("MIGRATION_OPERATION_OPT_IN", ""), ("MIGRATION_OPERATION_OPT_IN", "true"),
    ("AUTH_MODE", ""), ("MIGRATION_DATABASE_URL", ""),
    ("MIGRATION_DATABASE_URL", "not-a-url"),
])
def test_invalid_settings_fail_before_engine(monkeypatch, key, value):
    settings = synthetic_settings()
    settings[key] = value
    for name, setting in settings.items():
        monkeypatch.setenv(name, setting)
    with pytest.raises(RuntimeError, match="Online migration configuration") as error:
        run_online(None, None)
    assert "synthetic-only" not in str(error.value)
    assert not error.value.__cause__ and error.value.__suppress_context__


@pytest.mark.parametrize("changes", [
    {"host": "localhost"}, {"host": "192.0.2.1"}, {"port": 3307}, {"port": None},
    {"database": "company_db"}, {"database": "companyos_test"}, {"database": "other"},
    {"username": "root"}, {"username": "companyos_app"}, {"password": ""},
    {"query": {"charset": "utf8mb4"}}, {"drivername": "mysql"},
])
def test_wrong_target_or_account_refused_before_engine(monkeypatch, changes):
    settings = synthetic_settings()
    url = sqlalchemy.engine.make_url(settings["MIGRATION_DATABASE_URL"]).set(**changes)
    if "port" in changes and changes["port"] is None:
        url = sqlalchemy.URL.create(url.drivername, username=url.username, password=url.password,
                                    host=url.host, database=url.database)
    settings["MIGRATION_DATABASE_URL"] = url.render_as_string(hide_password=False)
    for key, value in settings.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match="Online migration configuration"):
        run_online(None, None)


def test_runtime_credentials_never_used_as_fallback():
    settings = synthetic_settings()
    settings["DATABASE_URL"] = settings.pop("MIGRATION_DATABASE_URL")
    with pytest.raises(RuntimeError, match="Online migration configuration"):
        migration_url(settings)


@pytest.mark.parametrize("missing", ["APP_ENV", "AUTH_MODE", "MIGRATION_OPERATION_OPT_IN", "MIGRATION_DATABASE_URL"])
def test_missing_required_input_is_refused(missing):
    settings = synthetic_settings()
    del settings[missing]
    with pytest.raises(RuntimeError, match="Online migration configuration"):
        migration_url(settings)


@pytest.mark.parametrize("suffix", ["#fragment", "?", "?charset=utf8mb4", "\n", "\t"])
def test_reuses_control_and_query_rejection(suffix):
    settings = synthetic_settings()
    settings["MIGRATION_DATABASE_URL"] += suffix
    with pytest.raises(RuntimeError, match="Online migration configuration") as error:
        migration_url(settings)
    assert "synthetic-only" not in str(error.value)


@pytest.mark.parametrize("failure", [None, "connect", "configure", "run", "dispose"])
def test_online_flow_with_fake_engine_and_sanitized_failures(monkeypatch, failure):
    for key, value in synthetic_settings().items():
        monkeypatch.setenv(key, value)
    events = []
    connection = object()

    class FakeEngine:
        @contextmanager
        def connect(self):
            events.append("connect")
            if failure == "connect":
                raise ValueError("synthetic-only")
            try:
                yield connection
            finally:
                events.append("close")

        def dispose(self):
            events.append("dispose")
            if failure == "dispose":
                raise ValueError("synthetic-only")

    def fake_create(url, **options):
        events.append("engine")
        assert url.username == "companyos_migrator"
        assert options["echo"] is False and options["hide_parameters"] is True
        assert options["poolclass"].__name__ == "NullPool"
        return FakeEngine()

    class FakeContext:
        def configure(self, **options):
            assert options == {"connection": connection, "target_metadata": "metadata"}
            events.append("configure")
            if failure == "configure":
                raise ValueError("synthetic-only")

        @contextmanager
        def begin_transaction(self):
            yield

        def run_migrations(self):
            events.append("run")
            if failure == "run":
                raise ValueError("synthetic-only")

    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create)
    if failure:
        with pytest.raises(RuntimeError, match="Online migration operation failed") as error:
            run_online(FakeContext(), "metadata")
        assert "synthetic-only" not in str(error.value)
        assert error.value.__suppress_context__
    else:
        run_online(FakeContext(), "metadata")
        assert events == ["engine", "connect", "configure", "run", "close", "dispose"]
    assert events[-1] == "dispose"
