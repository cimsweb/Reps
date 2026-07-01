import logging

from application.dto.authenticated_user import AuthenticatedUser
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from domain.exceptions import AuthorizationError, UnauthenticatedError
from domain.services.authorization import Permission, require_permission
from infrastructure.logging.setup import log_authorization_check


class AuthorizationGuard:
    """Authenticate requests and enforce role-based permissions."""

    def __init__(
        self,
        authenticate_session: AuthenticateSessionUseCase,
        logger: logging.Logger | None = None,
    ) -> None:
        self._authenticate_session = authenticate_session
        self._logger = logger or logging.getLogger("reps.auth")

    def authorize(self, token: str, permission: Permission) -> AuthenticatedUser:
        """Authenticate token and verify permission for the protected action."""
        authenticated_user: AuthenticatedUser | None = None
        try:
            authenticated_user = self._authenticate_session.execute(token)
            require_permission(authenticated_user.user, permission)
        except UnauthenticatedError as error:
            log_authorization_check(
                self._logger,
                success=False,
                user_id=None,
                role=None,
                route=permission.value,
            )
            raise error
        except AuthorizationError as error:
            log_authorization_check(
                self._logger,
                success=False,
                user_id=str(authenticated_user.user.id) if authenticated_user else None,
                role=authenticated_user.user.role.value if authenticated_user else None,
                route=permission.value,
            )
            raise error

        assert authenticated_user is not None
        log_authorization_check(
            self._logger,
            success=True,
            user_id=str(authenticated_user.user.id),
            role=authenticated_user.user.role.value,
            route=permission.value,
        )
        return authenticated_user
