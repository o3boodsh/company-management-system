"""Offline compilation or explicitly guarded, operator-only online execution."""

from alembic import context

from app.db.base import Base
from app.db import models  # Register all four tables; no engine construction.

target_metadata = Base.metadata


if context.is_offline_mode():
    context.configure(
        dialect_name="mysql",
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    from app.db.migration import run_online

    run_online(context, target_metadata)
