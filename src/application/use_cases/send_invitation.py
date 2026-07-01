import logging
from datetime import UTC, datetime
from uuid import uuid4

from domain.entities.invitation import Invitation
from domain.entities.invitation_status import InvitationStatus
from domain.entities.role import Role
from domain.exceptions import (
    AuthorizationError,
    CoachAthleteLinkAlreadyExistsError,
    DomainError,
    DuplicateInvitationError,
    InvalidInvitationTargetError,
)
from domain.repositories.coach_athlete_link_repository import CoachAthleteLinkRepository
from domain.repositories.invitation_repository import InvitationRepository
from domain.repositories.user_repository import UserRepository
from domain.value_objects.email import Email
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_coaching_event


class SendInvitationUseCase:
    """Coach sends an invitation to an athlete email."""

    def __init__(
        self,
        invitation_repository: InvitationRepository,
        link_repository: CoachAthleteLinkRepository,
        user_repository: UserRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._invitation_repository = invitation_repository
        self._link_repository = link_repository
        self._user_repository = user_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(self, coach_id: UserId, coach_role: Role, athlete_email: str) -> Invitation:
        """Create a pending invitation for an athlete email."""
        try:
            if coach_role is not Role.COACH:
                raise AuthorizationError("Only coaches can send invitations")

            validated_email = Email(athlete_email)
            coach = self._user_repository.get_by_id(coach_id)
            if coach is None:
                raise AuthorizationError("Coach account not found")
            if str(coach.email) == str(validated_email):
                raise InvalidInvitationTargetError("Coach cannot invite their own email")

            existing_user = self._user_repository.get_by_email(validated_email)
            if existing_user is not None and existing_user.role is not Role.ATHLETE:
                raise InvalidInvitationTargetError("Invitation target must be an athlete account")
            if existing_user is not None and self._link_repository.exists(
                coach_id,
                existing_user.id,
            ):
                raise CoachAthleteLinkAlreadyExistsError("Coach and athlete are already linked")

            if self._invitation_repository.get_pending_by_coach_and_email(
                coach_id,
                validated_email,
            ):
                raise DuplicateInvitationError(
                    f"Pending invitation already exists for {validated_email}"
                )

            invitation = Invitation(
                id=InvitationId(uuid4()),
                coach_id=coach_id,
                athlete_email=validated_email,
                status=InvitationStatus.PENDING,
                created_at=datetime.now(UTC),
            )
            saved_invitation = self._invitation_repository.save(invitation)
        except DomainError as error:
            log_coaching_event(
                self._logger,
                "coaching_validation_error",
                success=False,
                user_id=str(coach_id),
                message=str(error),
            )
            raise

        log_coaching_event(
            self._logger,
            "invitation_created",
            success=True,
            user_id=str(coach_id),
            message=f"Invitation sent to {validated_email}",
        )
        return saved_invitation
