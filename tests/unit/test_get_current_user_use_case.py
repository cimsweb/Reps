"""Tests for GetCurrentUserUseCase."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.use_cases.get_current_user import GetCurrentUserUseCase
from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import UnauthenticatedError
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId
from fakes.in_memory_repositories import InMemoryUserRepository


def test_get_current_user_returns_saved_user() -> None:
    repository = InMemoryUserRepository()
    user = repository.save(
        User(
            id=UserId(uuid4()),
            email=Email("coach@example.com"),
            password_hash=PasswordHash("hashed"),
            role=Role.COACH,
            created_at=datetime.now(UTC),
        )
    )

    result = GetCurrentUserUseCase(repository).execute(user.id)

    assert result.id == user.id
    assert result.role is Role.COACH


def test_get_current_user_rejects_missing_user() -> None:
    with pytest.raises(UnauthenticatedError):
        GetCurrentUserUseCase(InMemoryUserRepository()).execute(UserId(uuid4()))
