"""Integration tests for user query use cases."""

import os
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from application.security.authorization_guard import AuthorizationGuard
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from application.use_cases.get_current_user import GetCurrentUserUseCase
from application.use_cases.list_users import ListUsersUseCase
from application.use_cases.login_user import LoginUserUseCase
from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.role import Role
from domain.exceptions import AuthorizationError
from domain.services.authorization import Permission
from domain.value_objects.pagination import PageRequest
from infrastructure.db.engine import create_db_engine
from infrastructure.db.repositories import SqlAlchemySessionRepository, SqlAlchemyUserRepository
from infrastructure.db.seed_admin import seed_admin_user
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from infrastructure.security.sha256_session_token import Sha256SessionTokenService
from integration.conftest import database_is_available


def _build_guard(
    user_repository: SqlAlchemyUserRepository,
    session_repository: SqlAlchemySessionRepository,
) -> AuthorizationGuard:
    return AuthorizationGuard(
        AuthenticateSessionUseCase(
            user_repository,
            session_repository,
            Sha256SessionTokenService(),
        )
    )


@pytest.mark.integration
def test_coach_gets_own_profile_after_login() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    email = f"coach-{uuid4()}@example.com"
    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    token_service = Sha256SessionTokenService()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)
        RegisterUserUseCase(user_repository, hasher).execute(email, "secure1A", Role.COACH)
        login_result = LoginUserUseCase(
            user_repository,
            session_repository,
            hasher,
            token_service,
        ).execute(email, "secure1A")
        db_session.commit()

        auth_user = _build_guard(user_repository, session_repository).authorize(
            login_result.token,
            Permission.VIEW_OWN_ACCOUNT,
        )
        current_user = GetCurrentUserUseCase(user_repository).execute(auth_user.user.id)

        assert str(current_user.email) == email
        assert current_user.role is Role.COACH


@pytest.mark.integration
def test_admin_lists_users_with_pagination() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    os.environ.setdefault("ADMIN_PASSWORD", "secure1Admin")
    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    token_service = Sha256SessionTokenService()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)
        seed_admin_user(user_repository, hasher)
        for index in range(3):
            RegisterUserUseCase(user_repository, hasher).execute(
                f"athlete{index}-{uuid4()}@example.com",
                "secure1A",
                Role.ATHLETE,
            )
        login_result = LoginUserUseCase(
            user_repository,
            session_repository,
            hasher,
            token_service,
        ).execute(os.getenv("ADMIN_EMAIL", "admin@reps.local"), "secure1Admin")
        db_session.commit()

        _build_guard(user_repository, session_repository).authorize(
            login_result.token,
            Permission.LIST_USERS,
        )
        result = ListUsersUseCase(user_repository).execute(PageRequest(offset=0, limit=2))

        assert result.total >= 4
        assert len(result.items) == 2


@pytest.mark.integration
def test_coach_cannot_list_users_after_login() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    email = f"coach-{uuid4()}@example.com"
    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    token_service = Sha256SessionTokenService()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)
        RegisterUserUseCase(user_repository, hasher).execute(email, "secure1A", Role.COACH)
        login_result = LoginUserUseCase(
            user_repository,
            session_repository,
            hasher,
            token_service,
        ).execute(email, "secure1A")
        db_session.commit()

        with pytest.raises(AuthorizationError):
            _build_guard(user_repository, session_repository).authorize(
                login_result.token,
                Permission.LIST_USERS,
            )
