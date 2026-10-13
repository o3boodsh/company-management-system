"""Request cleanup with an explicitly supplied factory; no engine construction."""

from collections.abc import Callable, Iterator
import logging
from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger("companyos.sessions")


class SessionCleanupError(RuntimeError):
    """Signal failed cleanup without exposing driver/credential details."""


def session_scope(factory: Callable[[], "Session"]) -> Iterator["Session"]:
    session = factory()
    application_failed = False
    try:
        yield session
    except BaseException:
        application_failed = True
        raise
    finally:
        cleanup_failed = False
        try:
            if session.in_transaction():
                session.rollback()
        except Exception:
            cleanup_failed = True
        finally:
            try:
                session.close()
            except Exception:
                cleanup_failed = True
        if cleanup_failed:
            logger.warning("Session cleanup failed")
            if not application_failed:
                raise SessionCleanupError("Session cleanup failed") from None


def get_session(request: Request) -> Iterator["Session"]:
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise RuntimeError("Database sessions are not configured or authorized")
    yield from session_scope(factory)
