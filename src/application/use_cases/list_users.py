from application.dto.user_queries import PaginatedUsers, UserProfile
from domain.repositories.user_repository import UserRepository
from domain.value_objects.pagination import PageRequest


class ListUsersUseCase:
    """Return a paginated list of all users for admin queries."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, page: PageRequest | None = None) -> PaginatedUsers:
        """Load users sorted by newest registration first."""
        page_request = page or PageRequest()
        users = self._user_repository.list_page(
            offset=page_request.offset,
            limit=page_request.limit,
        )
        return PaginatedUsers(
            items=tuple(UserProfile.from_user(user) for user in users),
            total=self._user_repository.count_all(),
        )
