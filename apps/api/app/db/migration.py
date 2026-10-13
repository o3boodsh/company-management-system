"""Explicit operator-only migration boundary; importing never opens a connection."""

import os
from collections.abc import Mapping

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from app.core.config import ConfigurationError, load_settings


def migration_url(environ: Mapping[str, str] | None = None):
    source = os.environ if environ is None else environ
    try:
        if source.get("APP_ENV") != "local" or source.get("MIGRATION_OPERATION_OPT_IN") != "approved":
            raise ValueError()
        # Reuse strict DSN parsing without reading runtime/test credentials.
        settings = load_settings({
            key: source[key] for key in (
                "APP_ENV", "AUTH_MODE", "API_BIND_HOST", "DATASET_CONTEXT",
                "EXPECTED_DATABASE_NAME", "MIGRATION_DATABASE_URL",
            ) if key in source
        })
        if settings.migration_database_url is None or not settings.migration_database_url.get_secret_value():
            raise ValueError()
        url = make_url(settings.migration_database_url.get_secret_value())
        if not (
            url.drivername == "mysql+pymysql"
            and url.host == "127.0.0.1" and url.port == 3306
            and url.database == "companyos_dev"
            and url.username == "companyos_migrator" and bool(url.password)
            and not url.query
        ):
            raise ValueError()
        return url
    except (ConfigurationError, ValueError, ArgumentError):
        raise RuntimeError("Online migration configuration is missing, invalid or not opted in") from None


def run_online(context, metadata):
    url = migration_url()  # Must succeed before importing/calling engine creation.
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        engine = create_engine(
            url, poolclass=NullPool, echo=False, hide_parameters=True,
            connect_args={"connect_timeout": 5, "read_timeout": 10, "write_timeout": 10},
        )
        try:
            with engine.connect() as connection:
                context.configure(connection=connection, target_metadata=metadata)
                with context.begin_transaction():
                    context.run_migrations()
        finally:
            engine.dispose()
    except Exception:
        raise RuntimeError("Online migration operation failed; inspect state before retrying") from None
