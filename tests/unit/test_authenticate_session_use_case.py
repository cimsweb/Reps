"""Tests for AuthenticateSessionUseCase."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from domain.entities.role import Role
from domain.entities.session import Session
from domain.entities.user import User
from domain.exceptions import UnauthenticatedError
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId
from fakes.in_memory_repositories import InMemorySessionRepository, InMemoryUserRepository
from infrastructure.security.sha256_session_token import Sha256SessionTokenService


def _build_user() -> User:
    return User(
        id=UserId(uuid4()),
        email=Email("coach@example.com"),
        password_hash=PasswordHash("hashed"),
        role=Role.COACH,
        created_at=datetime.now(UTC),
    )


def test_authenticate_session_returns_authenticated_user() -> None:
    user_repository = InMemoryUserRepository()
    session_repository = InMemorySessionRepository()
    token_service = Sha256SessionTokenService()
    user = user_repository.save(_build_user())
    plain_token = token_service.generate()
    session_repository.save(
        Session(
            id=SessionId(uuid4()),
            user_id=user.id,
            token_hash=token_service.hash(plain_token),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            created_at=datetime.now(UTC),
        )
    )

    result = AuthenticateSessionUseCase(
        user_repository,
        session_repository,
        token_service,
    ).execute(plain_token)

    assert result.user.id == user.id
    assert result.session.user_id == user.id


def test_authenticate_session_rejects_unknown_token() -> None:
    use_case = AuthenticateSessionUseCase(
        InMemoryUserRepository(),
        InMemorySessionRepository(),
        Sha256SessionTokenService(),
    )

    with pytest.raises(UnauthenticatedError):
        use_case.execute("unknown-token")


def test_authenticate_session_rejects_expired_token() -> None:
    user_repository = InMemoryUserRepository()
    session_repository = InMemorySessionRepository()
    token_service = Sha256SessionTokenService()
    user = user_repository.save(_build_user())
    plain_token = token_service.generate()
    session_id = SessionId(uuid4())
    session_repository.save(
        Session(
            id=session_id,
            user_id=user.id,
            token_hash=token_service.hash(plain_token),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            created_at=datetime.now(UTC) - timedelta(days=1),
        )
    )

    with pytest.raises(UnauthenticatedError):
        AuthenticateSessionUseCase(
            user_repository,
            session_repository,
            token_service,
        ).execute(plain_token)

    assert session_repository.get_by_id(session_id) is None
