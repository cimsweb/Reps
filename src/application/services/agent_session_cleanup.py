"""Lazy cleanup helpers for agent sessions."""

from datetime import UTC, datetime, timedelta

from domain.repositories.agent_session_repository import AgentSessionRepository

ABANDONED_SESSION_RETENTION_DAYS = 7


def run_lazy_agent_session_cleanup(
    session_repository: AgentSessionRepository,
    *,
    now: datetime | None = None,
) -> int:
    """Abandon active sessions that exceeded inactivity expiry."""
    return session_repository.abandon_expired_active_sessions(now=now)


def is_abandoned_session_expired(
    updated_at: datetime,
    *,
    now: datetime | None = None,
    retention_days: int = ABANDONED_SESSION_RETENTION_DAYS,
) -> bool:
    """Return whether an abandoned session is older than retention policy."""
    current_time = now or datetime.now(UTC)
    return updated_at < current_time - timedelta(days=retention_days)
