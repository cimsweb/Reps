"""Authenticated request context."""

from dataclasses import dataclass

from domain.entities.session import Session
from domain.entities.user import User


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """User resolved from a valid session."""

    user: User
    session: Session
