"""Tests for password hashing infrastructure."""

from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher


def test_password_hasher_stores_hash_not_plain_text() -> None:
    hasher = ScryptPasswordHasher()
    password_hash = hasher.hash("secure1A")

    assert password_hash != "secure1A"
    assert password_hash.startswith("scrypt$")


def test_password_hasher_verifies_correct_password() -> None:
    hasher = ScryptPasswordHasher()
    password_hash = hasher.hash("secure1A")

    assert hasher.verify("secure1A", password_hash) is True
    assert hasher.verify("wrong-pass", password_hash) is False
