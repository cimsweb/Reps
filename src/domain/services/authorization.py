"""Authorization rules based on user roles."""

from enum import StrEnum

from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import AuthorizationError


class Permission(StrEnum):
    """Protected operations available in MVP 0."""

    LIST_USERS = "list_users"
    VIEW_OWN_ACCOUNT = "view_own_account"


_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset({Permission.LIST_USERS, Permission.VIEW_OWN_ACCOUNT}),
    Role.COACH: frozenset({Permission.VIEW_OWN_ACCOUNT}),
    Role.ATHLETE: frozenset({Permission.VIEW_OWN_ACCOUNT}),
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Return whether the role is allowed to perform the action."""
    return permission in _ROLE_PERMISSIONS[role]


def require_permission(user: User, permission: Permission) -> None:
    """Raise AuthorizationError when the user lacks the required permission."""
    if not has_permission(user.role, permission):
        raise AuthorizationError(
            f"Role '{user.role.value}' is not allowed to access '{permission.value}'"
        )
