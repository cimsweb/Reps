"""Tests for session token infrastructure."""

from infrastructure.security.sha256_session_token import Sha256SessionTokenService


def test_session_token_service_generates_unique_tokens() -> None:
    service = Sha256SessionTokenService()
    first = service.generate()
    second = service.generate()

    assert first != second
    assert len(first) > 20


def test_session_token_service_hashes_token() -> None:
    service = Sha256SessionTokenService()
    token = service.generate()
    token_hash = service.hash(token)

    assert token_hash != token
    assert len(token_hash) == 64
