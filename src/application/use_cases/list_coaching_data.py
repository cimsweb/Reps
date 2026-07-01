"""Use cases for MVP 1 read operations."""

from application.dto.coaching import (
    AthleteProfileView,
    CoachAthleteView,
    InvitationView,
    PaginatedPersonalRecords,
    PaginatedWorkoutFeedback,
    PersonalRecordView,
    WorkoutFeedbackView,
)
from application.security.coaching_access_guard import CoachingAccessGuard
from domain.entities.role import Role
from domain.exceptions import AthleteProfileNotFoundError, AuthorizationError
from domain.repositories.athlete_profile_repository import AthleteProfileRepository
from domain.repositories.coach_athlete_link_repository import CoachAthleteLinkRepository
from domain.repositories.invitation_repository import InvitationRepository
from domain.repositories.personal_record_repository import PersonalRecordRepository
from domain.repositories.workout_feedback_repository import WorkoutFeedbackRepository
from domain.value_objects.email import Email
from domain.value_objects.pagination import PageRequest
from domain.value_objects.user_id import UserId


class ListCoachInvitationsUseCase:
    """Return invitations created by a coach."""

    def __init__(self, invitation_repository: InvitationRepository) -> None:
        self._invitation_repository = invitation_repository

    def execute(self, coach_id: UserId, coach_role: Role) -> list[InvitationView]:
        if coach_role is not Role.COACH:
            raise AuthorizationError("Only coaches can list their invitations")

        invitations = self._invitation_repository.list_by_coach(coach_id)
        return [InvitationView.from_invitation(invitation) for invitation in invitations]


class ListPendingInvitationsUseCase:
    """Return pending invitations for an athlete email."""

    def __init__(self, invitation_repository: InvitationRepository) -> None:
        self._invitation_repository = invitation_repository

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        athlete_email: str,
    ) -> list[InvitationView]:
        if athlete_role is not Role.ATHLETE:
            raise AuthorizationError("Only athletes can list their invitations")

        _ = athlete_id
        invitations = self._invitation_repository.list_pending_for_email(Email(athlete_email))
        return [InvitationView.from_invitation(invitation) for invitation in invitations]


class ListCoachAthletesUseCase:
    """Return athletes linked to a coach."""

    def __init__(self, link_repository: CoachAthleteLinkRepository) -> None:
        self._link_repository = link_repository

    def execute(self, coach_id: UserId, coach_role: Role) -> list[CoachAthleteView]:
        if coach_role is not Role.COACH:
            raise AuthorizationError("Only coaches can list their athletes")

        links = self._link_repository.list_by_coach(coach_id)
        return [CoachAthleteView.from_link(link) for link in links]


class ListAthleteCoachesUseCase:
    """Return coaches linked to an athlete."""

    def __init__(self, link_repository: CoachAthleteLinkRepository) -> None:
        self._link_repository = link_repository

    def execute(self, athlete_id: UserId, athlete_role: Role) -> list[CoachAthleteView]:
        if athlete_role is not Role.ATHLETE:
            raise AuthorizationError("Only athletes can list their coaches")

        links = self._link_repository.list_by_athlete(athlete_id)
        return [CoachAthleteView.from_link(link) for link in links]


class GetAthleteProfileUseCase:
    """Return athlete profile for self or linked coach."""

    def __init__(
        self,
        profile_repository: AthleteProfileRepository,
        access_guard: CoachingAccessGuard,
    ) -> None:
        self._profile_repository = profile_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
    ) -> AthleteProfileView:
        self._ensure_access(actor_id, actor_role, athlete_id)

        profile = self._profile_repository.get_by_athlete_id(athlete_id)
        if profile is None:
            raise AthleteProfileNotFoundError(f"Athlete profile not found: {athlete_id.value}")

        return AthleteProfileView.from_profile(profile)

    def _ensure_access(self, actor_id: UserId, actor_role: Role, athlete_id: UserId) -> None:
        if actor_role is Role.ATHLETE:
            self._access_guard.ensure_athlete_owns_data(actor_id, athlete_id)
            return
        if actor_role is Role.COACH:
            self._access_guard.ensure_coach_can_access_athlete(actor_id, athlete_id)
            return
        raise AuthorizationError("Only coaches and athletes can view athlete profiles")


class ListPersonalRecordsUseCase:
    """Return personal records for an athlete."""

    def __init__(
        self,
        record_repository: PersonalRecordRepository,
        access_guard: CoachingAccessGuard,
    ) -> None:
        self._record_repository = record_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
        page: PageRequest | None = None,
    ) -> PaginatedPersonalRecords:
        self._ensure_access(actor_id, actor_role, athlete_id)

        page_request = page or PageRequest()
        records = self._record_repository.list_by_athlete_page(
            athlete_id,
            offset=page_request.offset,
            limit=page_request.limit,
        )
        return PaginatedPersonalRecords(
            items=tuple(PersonalRecordView.from_record(record) for record in records),
            total=self._record_repository.count_by_athlete(athlete_id),
        )

    def _ensure_access(self, actor_id: UserId, actor_role: Role, athlete_id: UserId) -> None:
        if actor_role is Role.ATHLETE:
            self._access_guard.ensure_athlete_owns_data(actor_id, athlete_id)
            return
        if actor_role is Role.COACH:
            self._access_guard.ensure_coach_can_access_athlete(actor_id, athlete_id)
            return
        raise AuthorizationError("Only coaches and athletes can view personal records")


class ListWorkoutFeedbackUseCase:
    """Return workout feedback history for an athlete."""

    def __init__(
        self,
        feedback_repository: WorkoutFeedbackRepository,
        access_guard: CoachingAccessGuard,
    ) -> None:
        self._feedback_repository = feedback_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
        page: PageRequest | None = None,
    ) -> PaginatedWorkoutFeedback:
        self._ensure_access(actor_id, actor_role, athlete_id)

        page_request = page or PageRequest()
        feedback_items = self._feedback_repository.list_by_athlete_page(
            athlete_id,
            offset=page_request.offset,
            limit=page_request.limit,
        )
        return PaginatedWorkoutFeedback(
            items=tuple(WorkoutFeedbackView.from_feedback(item) for item in feedback_items),
            total=self._feedback_repository.count_by_athlete(athlete_id),
        )

    def _ensure_access(self, actor_id: UserId, actor_role: Role, athlete_id: UserId) -> None:
        if actor_role is Role.ATHLETE:
            self._access_guard.ensure_athlete_owns_data(actor_id, athlete_id)
            return
        if actor_role is Role.COACH:
            self._access_guard.ensure_coach_can_access_athlete(actor_id, athlete_id)
            return
        raise AuthorizationError("Only coaches and athletes can view workout feedback")
