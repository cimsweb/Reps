from typing import Protocol

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.user_id import UserId


class UserRepository(Protocol):
    """Persistence contract for users."""

    def save(self, user: User) -> User:
        """Persist a user."""

    def get_by_id(self, user_id: UserId) -> User | None:
        """Load user by identifier."""

    def get_by_email(self, email: Email) -> User | None:
        """Load user by email."""

    def list_all(self) -> list[User]:
        """Return all users. Restricted to admin use cases."""

    def count_all(self) -> int:
        """Return total number of users."""

    def list_page(self, *, offset: int, limit: int) -> list[User]:
        """Return a page of users sorted by registration date descending."""
