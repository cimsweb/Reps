from typing import Protocol

from domain.entities.session import Session
from domain.value_objects.session_id import SessionId


class SessionRepository(Protocol):
    """Persistence contract for sessions."""

    def save(self, session: Session) -> Session:
        """Persist a session."""

    def get_by_id(self, session_id: SessionId) -> Session | None:
        """Load session by identifier."""

    def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Load session by hashed token value."""

    def delete(self, session_id: SessionId) -> None:
        """Remove a session."""
