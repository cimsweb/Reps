from enum import StrEnum

from domain.exceptions import InvalidRoleError


class Role(StrEnum):
    """System role assigned to a user."""

    ADMIN = "admin"
    COACH = "coach"
    ATHLETE = "athlete"

    @classmethod
    def from_registration(cls, value: str) -> "Role":
        """Return role allowed during self-registration."""
        try:
            role = cls(value)
        except ValueError as error:
            raise InvalidRoleError(f"Unknown role: {value}") from error

        if role is cls.ADMIN:
            raise InvalidRoleError("Admin role cannot be assigned during registration")

        return role
