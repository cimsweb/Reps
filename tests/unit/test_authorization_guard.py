"""Tests for AuthorizationGuard."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.security.authorization_guard import AuthorizationGuard
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from domain.entities.role import Role
from domain.entities.session import Session
from domain.entities.user import User
from domain.exceptions import AuthorizationError, UnauthenticatedError
from domain.services.authorization import Permission
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId
from fakes.in_memory_repositories import InMemorySessionRepository, InMemoryUserRepository
from infrastructure.security.sha256_session_token import Sha256SessionTokenService


def _build_guard(
    user_repository: InMemoryUserRepository,
    session_repository: InMemorySessionRepository,
    token_service: Sha256SessionTokenService,
) -> AuthorizationGuard:
    authenticate = AuthenticateSessionUseCase(
        user_repository,
        session_repository,
        token_service,
    )
    return AuthorizationGuard(authenticate)


def _create_session(
    user: User,
    session_repository: InMemorySessionRepository,
    token_service: Sha256SessionTokenService,
) -> str:
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
    return plain_token


def test_authorization_guard_allows_admin_to_list_users() -> None:
    user_repository = InMemoryUserRepository()
    session_repository = InMemorySessionRepository()
    token_service = Sha256SessionTokenService()
    admin = user_repository.save(
        User(
            id=UserId(uuid4()),
            email=Email("admin@example.com"),
            password_hash=PasswordHash("hashed"),
            role=Role.ADMIN,
            created_at=datetime.now(UTC),
        )
    )
    token = _create_session(admin, session_repository, token_service)

    result = _build_guard(user_repository, session_repository, token_service).authorize(
        token,
        Permission.LIST_USERS,
    )

    assert result.user.role is Role.ADMIN


def test_authorization_guard_rejects_coach_from_list_users() -> None:
    user_repository = InMemoryUserRepository()
    session_repository = InMemorySessionRepository()
    token_service = Sha256SessionTokenService()
    coach = user_repository.save(
        User(
            id=UserId(uuid4()),
            email=Email("coach@example.com"),
            password_hash=PasswordHash("hashed"),
            role=Role.COACH,
            created_at=datetime.now(UTC),
        )
    )
    token = _create_session(coach, session_repository, token_service)

    with pytest.raises(AuthorizationError):
        _build_guard(user_repository, session_repository, token_service).authorize(
            token,
            Permission.LIST_USERS,
        )


def test_authorization_guard_rejects_empty_token() -> None:
    guard = _build_guard(
        InMemoryUserRepository(),
        InMemorySessionRepository(),
        Sha256SessionTokenService(),
    )

    with pytest.raises(UnauthenticatedError):
        guard.authorize("", Permission.VIEW_OWN_ACCOUNT)
