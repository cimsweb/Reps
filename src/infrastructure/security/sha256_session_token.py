import hashlib
import secrets


class Sha256SessionTokenService:
    """Opaque session tokens with SHA-256 hashes for storage."""

    def generate(self) -> str:
        return secrets.token_urlsafe(32)

    def hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
