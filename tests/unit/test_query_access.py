"""Tests for query access rules combined with AuthorizationGuard."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from application.security.authorization_guard import AuthorizationGuard
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from application.use_cases.get_current_user import GetCurrentUserUseCase
from application.use_cases.list_users import ListUsersUseCase
from domain.entities.role import Role
from domain.entities.session import Session
from domain.entities.user import User
from domain.exceptions import AuthorizationError
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
) -> AuthorizationGuard:
    return AuthorizationGuard(
        AuthenticateSessionUseCase(
            user_repository,
            session_repository,
            Sha256SessionTokenService(),
        )
    )


def _create_token(
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


def test_coach_can_view_own_account() -> None:
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
    token = _create_token(coach, session_repository, token_service)

    auth_user = _build_guard(user_repository, session_repository).authorize(
        token,
        Permission.VIEW_OWN_ACCOUNT,
    )
    current_user = GetCurrentUserUseCase(user_repository).execute(auth_user.user.id)

    assert current_user.id == coach.id


def test_coach_cannot_list_users() -> None:
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
    token = _create_token(coach, session_repository, token_service)

    with pytest.raises(AuthorizationError):
        _build_guard(user_repository, session_repository).authorize(
            token,
            Permission.LIST_USERS,
        )


def test_admin_can_list_users() -> None:
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
    token = _create_token(admin, session_repository, token_service)

    _build_guard(user_repository, session_repository).authorize(token, Permission.LIST_USERS)
    result = ListUsersUseCase(user_repository).execute()

    assert result.total == 1
    assert result.items[0].email == "admin@example.com"
