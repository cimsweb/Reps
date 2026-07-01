from enum import StrEnum


class InvitationStatus(StrEnum):
    """Lifecycle status of a coach invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
