from dataclasses import dataclass
from datetime import datetime

from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class Session:
    """Authenticated user session backed by a token."""

    id: SessionId
    user_id: UserId
    token_hash: str
    expires_at: datetime
    created_at: datetime
