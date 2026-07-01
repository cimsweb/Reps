import logging
from datetime import UTC, datetime

from application.dto.authenticated_user import AuthenticatedUser
from domain.exceptions import UnauthenticatedError
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository
from domain.services.auth import SessionTokenService


class AuthenticateSessionUseCase:
    """Resolve a bearer token into an authenticated user."""

    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        session_token_service: SessionTokenService,
        logger: logging.Logger | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._session_token_service = session_token_service
        self._logger = logger or logging.getLogger("reps.auth")

    def execute(self, token: str) -> AuthenticatedUser:
        """Validate session token and return the authenticated user."""
        if not token.strip():
            raise UnauthenticatedError("Authentication token is required")

        token_hash = self._session_token_service.hash(token)
        session = self._session_repository.get_by_token_hash(token_hash)
        if session is None:
            raise UnauthenticatedError("Invalid authentication token")

        if session.expires_at <= datetime.now(UTC):
            self._session_repository.delete(session.id)
            raise UnauthenticatedError("Authentication token has expired")

        user = self._user_repository.get_by_id(session.user_id)
        if user is None:
            raise UnauthenticatedError("Invalid authentication token")

        return AuthenticatedUser(user=user, session=session)
