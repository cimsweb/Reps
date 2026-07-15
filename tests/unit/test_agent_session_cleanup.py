"""Unit tests for agent session cleanup helpers."""

from datetime import UTC, datetime, timedelta

from application.services.agent_session_cleanup import (
    ABANDONED_SESSION_RETENTION_DAYS,
    is_abandoned_session_expired,
)


def test_is_abandoned_session_expired() -> None:
    now = datetime.now(UTC)
    old = now - timedelta(days=ABANDONED_SESSION_RETENTION_DAYS + 1)
    recent = now - timedelta(days=1)
    assert is_abandoned_session_expired(old, now=now) is True
    assert is_abandoned_session_expired(recent, now=now) is False
