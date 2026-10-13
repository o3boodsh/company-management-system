"""Offline-only Alembic environment. Online execution is deliberately disabled."""

from alembic import context

from app.db.base import Base
from app.db import models  # Register all four tables; no engine construction.

target_metadata = Base.metadata


if not context.is_offline_mode():
    raise RuntimeError("Online Alembic execution is disabled; database access requires separate approval")

context.configure(
    dialect_name="mysql",
    target_metadata=target_metadata,
    literal_binds=True,
    dialect_opts={"paramstyle": "named"},
)
with context.begin_transaction():
    context.run_migrations()
