from dataclasses import dataclass
from datetime import datetime

from domain.entities.invitation_status import InvitationStatus
from domain.value_objects.email import Email
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class Invitation:
    """Coach invitation sent to an athlete email address."""

    id: InvitationId
    coach_id: UserId
    athlete_email: Email
    status: InvitationStatus
    created_at: datetime
    responded_at: datetime | None = None
