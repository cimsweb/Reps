from dataclasses import dataclass
from datetime import datetime

from domain.entities.role import Role
from domain.entities.user import User
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserProfile:
    """Public user data safe to return from queries."""

    id: UserId
    email: str
    role: Role
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserProfile":
        return cls(
            id=user.id,
            email=str(user.email),
            role=user.role,
            created_at=user.created_at,
        )


@dataclass(frozen=True, slots=True)
class PaginatedUsers:
    """Paginated list of user profiles."""

    items: tuple[UserProfile, ...]
    total: int
