"""Tests for role-based authorization rules."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import AuthorizationError
from domain.services.authorization import Permission, has_permission, require_permission
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId


def _build_user(role: Role) -> User:
    return User(
        id=UserId(uuid4()),
        email=Email(f"{role.value}@example.com"),
        password_hash=PasswordHash("hashed"),
        role=role,
        created_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("role", "permission", "expected"),
    [
        (Role.ADMIN, Permission.LIST_USERS, True),
        (Role.COACH, Permission.LIST_USERS, False),
        (Role.ATHLETE, Permission.LIST_USERS, False),
        (Role.ADMIN, Permission.VIEW_OWN_ACCOUNT, True),
        (Role.COACH, Permission.VIEW_OWN_ACCOUNT, True),
        (Role.ATHLETE, Permission.VIEW_OWN_ACCOUNT, True),
        (Role.COACH, Permission.VIEW_LINKED_ATHLETE_DATA, True),
        (Role.ATHLETE, Permission.MANAGE_OWN_COACHING_DATA, True),
        (Role.COACH, Permission.MANAGE_OWN_COACHING_DATA, False),
        (Role.ATHLETE, Permission.VIEW_LINKED_ATHLETE_DATA, False),
    ],
)
def test_has_permission(role: Role, permission: Permission, expected: bool) -> None:
    assert has_permission(role, permission) is expected


def test_require_permission_allows_admin_to_list_users() -> None:
    require_permission(_build_user(Role.ADMIN), Permission.LIST_USERS)


def test_require_permission_rejects_coach_from_list_users() -> None:
    with pytest.raises(AuthorizationError):
        require_permission(_build_user(Role.COACH), Permission.LIST_USERS)
