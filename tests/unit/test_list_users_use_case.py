"""Tests for ListUsersUseCase."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.list_users import ListUsersUseCase
from domain.entities.role import Role
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.pagination import DEFAULT_PAGE_SIZE, PageRequest
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId
from fakes.in_memory_repositories import InMemoryUserRepository


def _save_users(repository: InMemoryUserRepository, count: int) -> None:
    base_time = datetime.now(UTC)
    for index in range(count):
        repository.save(
            User(
                id=UserId(uuid4()),
                email=Email(f"user{index}@example.com"),
                password_hash=PasswordHash("hashed"),
                role=Role.ATHLETE,
                created_at=base_time - timedelta(minutes=index),
            )
        )


def test_list_users_returns_newest_first() -> None:
    repository = InMemoryUserRepository()
    _save_users(repository, 3)

    result = ListUsersUseCase(repository).execute()

    assert result.total == 3
    assert len(result.items) == 3
    assert result.items[0].email == "user0@example.com"
    assert result.items[2].email == "user2@example.com"


def test_list_users_paginates_results() -> None:
    repository = InMemoryUserRepository()
    _save_users(repository, 25)

    first_page = ListUsersUseCase(repository).execute(PageRequest(offset=0, limit=20))
    second_page = ListUsersUseCase(repository).execute(PageRequest(offset=20, limit=20))

    assert first_page.total == 25
    assert len(first_page.items) == 20
    assert len(second_page.items) == 5


def test_list_users_rejects_invalid_page_request() -> None:
    with pytest.raises(ValueError):
        PageRequest(offset=-1)


def test_list_users_uses_default_page_size() -> None:
    repository = InMemoryUserRepository()
    _save_users(repository, DEFAULT_PAGE_SIZE + 5)

    result = ListUsersUseCase(repository).execute()

    assert len(result.items) == DEFAULT_PAGE_SIZE
    assert result.total == DEFAULT_PAGE_SIZE + 5
