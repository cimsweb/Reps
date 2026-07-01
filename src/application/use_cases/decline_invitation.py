import logging
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from domain.entities.invitation import Invitation
from domain.entities.invitation_status import InvitationStatus
from domain.entities.role import Role
from domain.exceptions import (
    AuthorizationError,
    DomainError,
    InvitationAlreadyRespondedError,
    InvitationEmailMismatchError,
    InvitationNotFoundError,
)
from domain.repositories.invitation_repository import InvitationRepository
from domain.value_objects.email import Email
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_coaching_event


class DeclineInvitationUseCase:
    """Athlete declines a pending invitation."""

    def __init__(
        self,
        invitation_repository: InvitationRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._invitation_repository = invitation_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        athlete_email: str,
        invitation_id: str,
    ) -> Invitation:
        """Decline a pending invitation."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can decline invitations")

            invitation = self._invitation_repository.get_by_id(InvitationId(UUID(invitation_id)))
            if invitation is None:
                raise InvitationNotFoundError(f"Invitation not found: {invitation_id}")
            if invitation.status is not InvitationStatus.PENDING:
                raise InvitationAlreadyRespondedError("Invitation was already responded to")
            if str(invitation.athlete_email) != str(Email(athlete_email)):
                raise InvitationEmailMismatchError(
                    "Invitation email does not match athlete account"
                )

            saved_invitation = self._invitation_repository.save(
                replace(
                    invitation,
                    status=InvitationStatus.DECLINED,
                    responded_at=datetime.now(UTC),
                )
            )
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
            "invitation_declined",
            success=True,
            user_id=str(athlete_id),
            message=f"Invitation {invitation_id} declined",
        )
        return saved_invitation
