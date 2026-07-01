from dataclasses import dataclass
from datetime import datetime

from domain.entities.role import Role
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class User:
    """Authenticated system user."""

    id: UserId
    email: Email
    password_hash: PasswordHash
    role: Role
    created_at: datetime
