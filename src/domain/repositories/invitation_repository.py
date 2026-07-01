from typing import Protocol

from domain.entities.invitation import Invitation
from domain.entities.invitation_status import InvitationStatus
from domain.value_objects.email import Email
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.user_id import UserId


class InvitationRepository(Protocol):
    """Persistence contract for coach invitations."""

    def save(self, invitation: Invitation) -> Invitation:
        """Persist an invitation."""

    def get_by_id(self, invitation_id: InvitationId) -> Invitation | None:
        """Load invitation by identifier."""

    def get_pending_by_coach_and_email(
        self,
        coach_id: UserId,
        athlete_email: Email,
    ) -> Invitation | None:
        """Load pending invitation for coach and athlete email."""

    def list_by_coach(self, coach_id: UserId) -> list[Invitation]:
        """Return all invitations created by a coach."""

    def list_by_coach_and_status(
        self,
        coach_id: UserId,
        status: InvitationStatus,
    ) -> list[Invitation]:
        """Return coach invitations filtered by status."""

    def list_pending_for_email(self, athlete_email: Email) -> list[Invitation]:
        """Return pending invitations addressed to an email."""
