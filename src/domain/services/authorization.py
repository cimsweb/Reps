"""Authorization rules based on user roles."""

from enum import StrEnum

from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import AuthorizationError


class Permission(StrEnum):
    """Protected operations available in the application."""

    LIST_USERS = "list_users"
    VIEW_OWN_ACCOUNT = "view_own_account"
    MANAGE_OWN_COACHING_DATA = "manage_own_coaching_data"
    VIEW_LINKED_ATHLETE_DATA = "view_linked_athlete_data"
    MANAGE_TRAINING_PLANS = "manage_training_plans"
    VIEW_OWN_TRAINING_PLAN = "view_own_training_plan"
    SUBMIT_WORKOUT_REPORT = "submit_workout_report"
    VIEW_LINKED_ATHLETE_TRAINING = "view_linked_athlete_training"


_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(
        {
            Permission.LIST_USERS,
            Permission.VIEW_OWN_ACCOUNT,
        }
    ),
    Role.COACH: frozenset(
        {
            Permission.VIEW_OWN_ACCOUNT,
            Permission.VIEW_LINKED_ATHLETE_DATA,
            Permission.MANAGE_TRAINING_PLANS,
            Permission.VIEW_LINKED_ATHLETE_TRAINING,
        }
    ),
    Role.ATHLETE: frozenset(
        {
            Permission.VIEW_OWN_ACCOUNT,
            Permission.MANAGE_OWN_COACHING_DATA,
            Permission.VIEW_OWN_TRAINING_PLAN,
            Permission.SUBMIT_WORKOUT_REPORT,
        }
    ),
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
