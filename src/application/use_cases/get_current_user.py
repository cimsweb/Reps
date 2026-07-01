from domain.entities.user import User
from domain.exceptions import UnauthenticatedError
from domain.repositories.user_repository import UserRepository
from domain.value_objects.user_id import UserId


class GetCurrentUserUseCase:
    """Load the authenticated user."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, user_id: UserId) -> User:
        """Return the user linked to the active session."""
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise UnauthenticatedError("Invalid authentication token")
        return user
