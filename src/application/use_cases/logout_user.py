import logging

from domain.repositories.session_repository import SessionRepository
from domain.value_objects.session_id import SessionId
from infrastructure.logging.setup import log_auth_event


class LogoutUserUseCase:
    """Terminate an authenticated session."""

    def __init__(
        self,
        session_repository: SessionRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._logger = logger or logging.getLogger("reps.auth")

    def execute(self, session_id: SessionId) -> None:
        """Invalidate a session. Missing sessions are ignored."""
        session = self._session_repository.get_by_id(session_id)
        if session is None:
            log_auth_event(
                self._logger,
                event="logout",
                success=False,
                message="Session not found",
            )
            return

        self._session_repository.delete(session_id)
        log_auth_event(
            self._logger,
            event="logout",
            success=True,
            user_id=str(session.user_id),
            message="User logged out",
        )
