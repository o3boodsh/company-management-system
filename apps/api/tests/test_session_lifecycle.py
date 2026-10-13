"""Persistence cleanup verified exclusively with in-memory fake sessions."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.db.session import SessionCleanupError, get_session, session_scope


class FakeSession:
    def __init__(self, active=True, rollback_failure=False, close_failure=False):
        self.active = active
        self.rollback_failure = rollback_failure
        self.close_failure = close_failure
        self.calls = []

    def in_transaction(self):
        return self.active

    def rollback(self):
        self.calls.append("rollback")
        if self.rollback_failure:
            raise RuntimeError("Synthetic rollback failure")

    def close(self):
        self.calls.append("close")
        if self.close_failure:
            raise RuntimeError("Synthetic close failure")

    def commit(self):
        self.calls.append("commit")


@pytest.mark.parametrize("active", [True, False])
def test_success_closes_and_rolls_back_only_unfinished_work(active):
    fake = FakeSession(active)
    with contextmanager(session_scope)(lambda: fake) as session:
        assert session is fake
    assert fake.calls == (["rollback", "close"] if active else ["close"])


def test_failure_rolls_back_closes_and_preserves_failure():
    fake = FakeSession()
    with pytest.raises(ValueError, match="Synthetic service failure"):
        with contextmanager(session_scope)(lambda: fake):
            raise ValueError("Synthetic service failure")
    assert fake.calls == ["rollback", "close"]


def test_close_still_happens_when_rollback_fails():
    fake = FakeSession(rollback_failure=True)
    with pytest.raises(SessionCleanupError, match="Session cleanup failed"):
        with contextmanager(session_scope)(lambda: fake):
            pass
    assert fake.calls == ["rollback", "close"]


def test_unconfigured_dependency_cannot_open_database():
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(session_factory=None)))
    with pytest.raises(RuntimeError, match="not configured or authorized"):
        next(get_session(request))


def test_each_request_gets_its_own_session_without_commit():
    created = []

    def factory():
        fake = FakeSession()
        created.append(fake)
        return fake

    for _ in range(2):
        with contextmanager(session_scope)(factory):
            pass
    assert created[0] is not created[1]
    assert all(fake.calls == ["rollback", "close"] for fake in created)


@pytest.mark.parametrize("rollback_failure,close_failure", [(True, False), (False, True), (True, True)])
def test_cleanup_failure_preserves_the_original_service_exception(rollback_failure, close_failure, caplog):
    fake = FakeSession(rollback_failure=rollback_failure, close_failure=close_failure)
    original = ValueError("Synthetic service failure")
    with pytest.raises(ValueError) as failure:
        with contextmanager(session_scope)(lambda: fake):
            raise original
    assert failure.value is original
    assert fake.calls == ["rollback", "close"]
    assert "Synthetic rollback failure" not in caplog.text
    assert "Synthetic close failure" not in caplog.text
    assert "Synthetic service failure" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records if record.name == "companyos.sessions")


@pytest.mark.parametrize("rollback_failure,close_failure", [(True, False), (False, True), (True, True)])
def test_cleanup_failure_without_service_failure_is_reported_safely(rollback_failure, close_failure, caplog):
    fake = FakeSession(rollback_failure=rollback_failure, close_failure=close_failure)
    with pytest.raises(SessionCleanupError) as failure:
        with contextmanager(session_scope)(lambda: fake):
            pass
    assert str(failure.value) == "Session cleanup failed"
    assert failure.value.__suppress_context__
    assert fake.calls == ["rollback", "close"]
    assert "Synthetic rollback failure" not in caplog.text
    assert "Synthetic close failure" not in caplog.text


def test_close_failure_without_active_transaction_is_not_swallowed():
    fake = FakeSession(active=False, close_failure=True)
    with pytest.raises(SessionCleanupError):
        with contextmanager(session_scope)(lambda: fake):
            pass
    assert fake.calls == ["close"]


def test_driver_secrets_in_cleanup_failures_are_not_reported_or_logged(caplog):
    class SensitiveFake(FakeSession):
        def rollback(self):
            self.calls.append("rollback")
            raise RuntimeError("mysql://synthetic-user:synthetic-password@example.invalid/companyos_dev")

        def close(self):
            self.calls.append("close")
            raise RuntimeError("synthetic-password")

    fake = SensitiveFake()
    with pytest.raises(SessionCleanupError) as failure:
        with contextmanager(session_scope)(lambda: fake):
            pass
    assert fake.calls == ["rollback", "close"]
    assert "synthetic-password" not in str(failure.value) + repr(failure.value) + caplog.text
    assert "mysql://" not in str(failure.value) + caplog.text
