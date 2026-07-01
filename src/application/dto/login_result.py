"""Data transfer objects for application layer."""

from dataclasses import dataclass
from datetime import datetime

from domain.entities.user import User


@dataclass(frozen=True, slots=True)
class LoginResult:
    """Successful login payload returned to the transport layer."""

    token: str
    expires_at: datetime
    user: User
