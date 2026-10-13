"""Declarative metadata only; no engine, sessions, or schema creation."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
