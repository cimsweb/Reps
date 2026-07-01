import logging
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.invitation import Invitation
from domain.entities.invitation_status import InvitationStatus
from domain.entities.role import Role
from domain.exceptions import (
    AuthorizationError,
    CoachAthleteLinkAlreadyExistsError,
    DomainError,
    InvitationAlreadyRespondedError,
    InvitationEmailMismatchError,
    InvitationNotFoundError,
)
from domain.repositories.coach_athlete_link_repository import CoachAthleteLinkRepository
from domain.repositories.invitation_repository import InvitationRepository
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.email import Email
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_coaching_event


class AcceptInvitationUseCase:
    """Athlete accepts a pending invitation."""

    def __init__(
        self,
        invitation_repository: InvitationRepository,
        link_repository: CoachAthleteLinkRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._invitation_repository = invitation_repository
        self._link_repository = link_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        athlete_email: str,
        invitation_id: str,
    ) -> CoachAthleteLink:
        """Accept invitation and create coach-athlete link.

        Caller must run this use case inside a single database transaction so
        invitation status and link creation commit or roll back together.
        """
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can accept invitations")

            invitation = self._load_pending_invitation(invitation_id)
            self._ensure_invitee(invitation, athlete_id, athlete_email)

            if self._link_repository.exists(invitation.coach_id, athlete_id):
                raise CoachAthleteLinkAlreadyExistsError("Coach and athlete are already linked")

            responded_at = datetime.now(UTC)
            self._invitation_repository.save(
                replace(
                    invitation,
                    status=InvitationStatus.ACCEPTED,
                    responded_at=responded_at,
                )
            )

            link = CoachAthleteLink(
                id=CoachAthleteLinkId(uuid4()),
                coach_id=invitation.coach_id,
                athlete_id=athlete_id,
                created_at=responded_at,
            )
            saved_link = self._link_repository.save(link)
        except DomainError as error:
            log_coaching_event(
                self._logger,
                "coaching_validation_error",
                success=False,
                user_id=str(athlete_id),
                message=str(error),
            )
            raise

        log_coaching_event(
            self._logger,
            "invitation_accepted",
            success=True,
            user_id=str(athlete_id),
            message=f"Invitation {invitation_id} accepted",
        )
        return saved_link

    def _load_pending_invitation(self, invitation_id: str) -> Invitation:
        invitation = self._invitation_repository.get_by_id(InvitationId(UUID(invitation_id)))
        if invitation is None:
            raise InvitationNotFoundError(f"Invitation not found: {invitation_id}")
        if invitation.status is not InvitationStatus.PENDING:
            raise InvitationAlreadyRespondedError("Invitation was already responded to")
        return invitation

    def _ensure_invitee(
        self,
        invitation: Invitation,
        athlete_id: UserId,
        athlete_email: str,
    ) -> None:
        if invitation.coach_id == athlete_id:
            raise InvitationEmailMismatchError("Coach cannot accept their own invitation")
        if str(invitation.athlete_email) != str(Email(athlete_email)):
            raise InvitationEmailMismatchError("Invitation email does not match athlete account")
