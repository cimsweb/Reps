from datetime import timedelta
from typing import Protocol


class PasswordHasher(Protocol):
    """Hash and verify passwords without storing plain text."""

    def hash(self, password: str) -> str:
        """Return a stored password hash."""

    def verify(self, password: str, password_hash: str) -> bool:
        """Check whether password matches the stored hash."""


class SessionTokenService(Protocol):
    """Generate opaque session tokens and their stored hashes."""

    def generate(self) -> str:
        """Return a new opaque session token."""

    def hash(self, token: str) -> str:
        """Return a stored hash for the token."""


SESSION_LIFETIME = timedelta(days=30)

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"
