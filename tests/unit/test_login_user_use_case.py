"""Tests for LoginUserUseCase."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.use_cases.login_user import LoginUserUseCase
from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import AuthenticationError
from domain.services.auth import INVALID_CREDENTIALS_MESSAGE
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId
from fakes.in_memory_repositories import InMemorySessionRepository, InMemoryUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from infrastructure.security.sha256_session_token import Sha256SessionTokenService


def _build_login_use_case(
    user_repository: InMemoryUserRepository,
    session_repository: InMemorySessionRepository,
) -> LoginUserUseCase:
    return LoginUserUseCase(
        user_repository,
        session_repository,
        ScryptPasswordHasher(),
        Sha256SessionTokenService(),
    )


def test_login_user_returns_session_token() -> None:
    user_repository = InMemoryUserRepository()
    session_repository = InMemorySessionRepository()
    RegisterUserUseCase(user_repository, ScryptPasswordHasher()).execute(
        "coach@example.com",
        "secure1A",
        Role.COACH,
    )

    result = _build_login_use_case(user_repository, session_repository).execute(
        "coach@example.com",
        "secure1A",
    )

    assert result.token
    assert result.user.role is Role.COACH
    assert result.expires_at > datetime.now(UTC)
    stored_session = session_repository.get_by_token_hash(
        Sha256SessionTokenService().hash(result.token)
    )
    assert stored_session is not None


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("missing@example.com", "secure1A"),
        ("coach@example.com", "wrong-pass"),
    ],
)
def test_login_user_rejects_invalid_credentials(email: str, password: str) -> None:
    user_repository = InMemoryUserRepository()
    session_repository = InMemorySessionRepository()
    hasher = ScryptPasswordHasher()
    user_repository.save(
        User(
            id=UserId(uuid4()),
            email=Email("coach@example.com"),
            password_hash=PasswordHash(hasher.hash("secure1A")),
            role=Role.COACH,
            created_at=datetime.now(UTC),
        )
    )

    with pytest.raises(AuthenticationError, match=INVALID_CREDENTIALS_MESSAGE):
        _build_login_use_case(user_repository, session_repository).execute(email, password)
