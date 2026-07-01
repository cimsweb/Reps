"""Integration tests for authorization flow."""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from application.security.authorization_guard import AuthorizationGuard
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from application.use_cases.login_user import LoginUserUseCase
from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, UnauthenticatedError
from domain.services.authorization import Permission
from infrastructure.db.engine import create_db_engine
from infrastructure.db.repositories import SqlAlchemySessionRepository, SqlAlchemyUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from infrastructure.security.sha256_session_token import Sha256SessionTokenService
from integration.admin_helpers import (
    create_test_admin_email,
    login_test_admin,
    seed_test_admin,
)
from integration.conftest import database_is_available


def _build_guard(
    user_repository: SqlAlchemyUserRepository,
    session_repository: SqlAlchemySessionRepository,
) -> AuthorizationGuard:
    token_service = Sha256SessionTokenService()
    authenticate = AuthenticateSessionUseCase(
        user_repository,
        session_repository,
        token_service,
    )
    return AuthorizationGuard(authenticate)


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


@pytest.mark.integration
def test_admin_can_list_users_after_seed() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    admin_email = create_test_admin_email()
    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    token_service = Sha256SessionTokenService()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)
        seed_test_admin(user_repository, hasher, admin_email)
        login_result = login_test_admin(
            user_repository,
            session_repository,
            hasher,
            token_service,
            admin_email,
        )
        db_session.commit()

        result = _build_guard(user_repository, session_repository).authorize(
            login_result.token,
            Permission.LIST_USERS,
        )

        assert result.user.role is Role.ADMIN


@pytest.mark.integration
def test_invalid_token_is_rejected() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)

        with pytest.raises(UnauthenticatedError):
            _build_guard(user_repository, session_repository).authorize(
                "invalid-token",
                Permission.VIEW_OWN_ACCOUNT,
            )
