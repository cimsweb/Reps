"""Unit tests for domain layer."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain.entities.role import Role
from domain.entities.session import Session
from domain.entities.user import User
from domain.exceptions import InvalidEmailError, InvalidRoleError
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId


def test_email_normalizes_value() -> None:
    email = Email("  Coach@Example.COM  ")
    assert str(email) == "coach@example.com"


def test_email_rejects_invalid_format() -> None:
    with pytest.raises(InvalidEmailError):
        Email("not-an-email")


def test_role_from_registration_allows_coach_and_athlete() -> None:
    assert Role.from_registration("coach") is Role.COACH
    assert Role.from_registration("athlete") is Role.ATHLETE


def test_role_from_registration_rejects_admin() -> None:
    with pytest.raises(InvalidRoleError):
        Role.from_registration("admin")


def test_user_entity_holds_value_objects() -> None:
    user_id = UserId(uuid4())
    created_at = datetime.now(UTC)
    user = User(
        id=user_id,
        email=Email("athlete@example.com"),
        password_hash=PasswordHash("hashed-secret"),
        role=Role.ATHLETE,
        created_at=created_at,
    )

    assert user.id == user_id
    assert user.role is Role.ATHLETE


def test_session_entity_holds_token_hash() -> None:
    session = Session(
        id=SessionId(uuid4()),
        user_id=UserId(uuid4()),
        token_hash="token-hash",
        expires_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )

    assert session.token_hash == "token-hash"
