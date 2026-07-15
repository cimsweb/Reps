from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from application.security.authorization_guard import AuthorizationGuard
from application.security.coaching_access_guard import CoachingAccessGuard
from application.security.training_access_guard import TrainingAccessGuard
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from infrastructure.db.coaching_repositories import SqlAlchemyCoachAthleteLinkRepository
from infrastructure.db.engine import create_db_engine
from infrastructure.db.repositories import SqlAlchemySessionRepository, SqlAlchemyUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from infrastructure.security.sha256_session_token import Sha256SessionTokenService


def get_db() -> Generator[Session]:
    """Provide a database session per request."""
    engine = create_db_engine()
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_password_hasher() -> ScryptPasswordHasher:
    return ScryptPasswordHasher()


def get_session_token_service() -> Sha256SessionTokenService:
    return Sha256SessionTokenService()


def build_authorization_guard(db: Session) -> AuthorizationGuard:
    user_repository = SqlAlchemyUserRepository(db)
    session_repository = SqlAlchemySessionRepository(db)
    authenticate_session = AuthenticateSessionUseCase(
        user_repository,
        session_repository,
        Sha256SessionTokenService(),
    )
    return AuthorizationGuard(authenticate_session)


def get_authorization_guard(db: DbSession) -> AuthorizationGuard:
    return build_authorization_guard(db)


AuthorizationGuardDep = Annotated[AuthorizationGuard, Depends(get_authorization_guard)]


def get_coaching_access_guard(db: DbSession) -> CoachingAccessGuard:
    return CoachingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db))


CoachingAccessGuardDep = Annotated[CoachingAccessGuard, Depends(get_coaching_access_guard)]


def get_training_access_guard(db: DbSession) -> TrainingAccessGuard:
    return TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db))


TrainingAccessGuardDep = Annotated[TrainingAccessGuard, Depends(get_training_access_guard)]


def get_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthenticated", "message": "Authentication token is required"},
        )
    return authorization.removeprefix("Bearer ").strip()
