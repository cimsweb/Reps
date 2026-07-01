"""Integration tests for authentication data ingestion."""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session as OrmSession

from application.use_cases.login_user import LoginUserUseCase
from application.use_cases.logout_user import LogoutUserUseCase
from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.role import Role
from domain.exceptions import AuthenticationError
from domain.value_objects.session_id import SessionId
from infrastructure.db.engine import get_database_url
from infrastructure.db.models import SessionRecord, UserRecord
from infrastructure.db.repositories import SqlAlchemySessionRepository, SqlAlchemyUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from infrastructure.security.sha256_session_token import Sha256SessionTokenService
from integration.conftest import database_is_available


@pytest.mark.integration
def test_register_login_logout_persist_to_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    email = f"integration-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()
    token_service = Sha256SessionTokenService()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)

        user = RegisterUserUseCase(user_repository, hasher).execute(
            email,
            "secure1A",
            Role.ATHLETE,
        )
        db_session.commit()

        user_record = db_session.scalar(select(UserRecord).where(UserRecord.id == user.id.value))
        assert user_record is not None
        assert user_record.password_hash != "secure1A"

        login_result = LoginUserUseCase(
            user_repository,
            session_repository,
            hasher,
            token_service,
        ).execute(email, "secure1A")
        db_session.commit()

        token_hash = token_service.hash(login_result.token)
        session_record = db_session.scalar(
            select(SessionRecord).where(SessionRecord.token_hash == token_hash)
        )
        assert session_record is not None
        assert session_record.token_hash != login_result.token

        LogoutUserUseCase(session_repository).execute(SessionId(session_record.id))
        db_session.commit()

        deleted_session = db_session.scalar(
            select(SessionRecord).where(SessionRecord.id == session_record.id)
        )
        assert deleted_session is None


@pytest.mark.integration
def test_login_rejects_invalid_credentials_in_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    email = f"integration-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        session_repository = SqlAlchemySessionRepository(db_session)
        RegisterUserUseCase(user_repository, hasher).execute(email, "secure1A", Role.COACH)
        db_session.commit()

        use_case = LoginUserUseCase(
            user_repository,
            session_repository,
            hasher,
            Sha256SessionTokenService(),
        )

        with pytest.raises(AuthenticationError):
            use_case.execute(email, "wrong-pass")
