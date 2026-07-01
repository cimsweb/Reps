import logging
from datetime import UTC, datetime
from uuid import uuid4

from application.dto.login_result import LoginResult
from domain.entities.session import Session
from domain.exceptions import AuthenticationError, DomainError
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository
from domain.services.auth import (
    INVALID_CREDENTIALS_MESSAGE,
    SESSION_LIFETIME,
    PasswordHasher,
    SessionTokenService,
)
from domain.value_objects.email import Email
from domain.value_objects.session_id import SessionId
from infrastructure.logging.setup import log_auth_event


class LoginUserUseCase:
    """Authenticate a user and create a session."""

    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        password_hasher: PasswordHasher,
        session_token_service: SessionTokenService,
        logger: logging.Logger | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._password_hasher = password_hasher
        self._session_token_service = session_token_service
        self._logger = logger or logging.getLogger("reps.auth")

    def execute(self, email: str, password: str) -> LoginResult:
        """Validate credentials and open a session."""
        try:
            validated_email = Email(email)
            user = self._user_repository.get_by_email(validated_email)
            password_matches = user is not None and self._password_hasher.verify(
                password,
                str(user.password_hash),
            )
            if user is None or not password_matches:
                raise AuthenticationError(INVALID_CREDENTIALS_MESSAGE)

            plain_token = self._session_token_service.generate()
            token_hash = self._session_token_service.hash(plain_token)
            created_at = datetime.now(UTC)
            session = Session(
                id=SessionId(uuid4()),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=created_at + SESSION_LIFETIME,
                created_at=created_at,
            )
            self._session_repository.save(session)
        except DomainError as error:
            log_auth_event(
                self._logger,
                event="login",
                success=False,
                message=str(error),
            )
            raise

        log_auth_event(
            self._logger,
            event="login",
            success=True,
            user_id=str(user.id),
            role=user.role.value,
            message="User logged in",
        )
        return LoginResult(token=plain_token, expires_at=session.expires_at, user=user)
