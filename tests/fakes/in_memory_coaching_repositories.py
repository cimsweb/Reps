"""In-memory coaching repository fakes for unit tests."""

from domain.entities.athlete_profile import AthleteProfile
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.invitation import Invitation
from domain.entities.invitation_status import InvitationStatus
from domain.entities.personal_record import PersonalRecord
from domain.entities.record_type import RecordType
from domain.entities.workout_feedback import WorkoutFeedback
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.email import Email
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.personal_record_id import PersonalRecordId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_feedback_id import WorkoutFeedbackId


class InMemoryInvitationRepository:
    """Simple in-memory InvitationRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[InvitationId, Invitation] = {}

    def save(self, invitation: Invitation) -> Invitation:
        self._by_id[invitation.id] = invitation
        return invitation

    def get_by_id(self, invitation_id: InvitationId) -> Invitation | None:
        return self._by_id.get(invitation_id)

    def get_pending_by_coach_and_email(
        self,
        coach_id: UserId,
        athlete_email: Email,
    ) -> Invitation | None:
        for invitation in self._by_id.values():
            if (
                invitation.coach_id == coach_id
                and str(invitation.athlete_email) == str(athlete_email)
                and invitation.status is InvitationStatus.PENDING
            ):
                return invitation
        return None

    def list_by_coach(self, coach_id: UserId) -> list[Invitation]:
        return [
            invitation for invitation in self._by_id.values() if invitation.coach_id == coach_id
        ]

    def list_by_coach_and_status(
        self,
        coach_id: UserId,
        status: InvitationStatus,
    ) -> list[Invitation]:
        return [
            invitation
            for invitation in self._by_id.values()
            if invitation.coach_id == coach_id and invitation.status is status
        ]

    def list_pending_for_email(self, athlete_email: Email) -> list[Invitation]:
        return [
            invitation
            for invitation in self._by_id.values()
            if str(invitation.athlete_email) == str(athlete_email)
            and invitation.status is InvitationStatus.PENDING
        ]


class InMemoryCoachAthleteLinkRepository:
    """Simple in-memory CoachAthleteLinkRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[CoachAthleteLinkId, CoachAthleteLink] = {}

    def save(self, link: CoachAthleteLink) -> CoachAthleteLink:
        self._by_id[link.id] = link
        return link

    def exists(self, coach_id: UserId, athlete_id: UserId) -> bool:
        return self.get_by_coach_and_athlete(coach_id, athlete_id) is not None

    def get_by_coach_and_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> CoachAthleteLink | None:
        for link in self._by_id.values():
            if link.coach_id == coach_id and link.athlete_id == athlete_id:
                return link
        return None

    def list_by_coach(self, coach_id: UserId) -> list[CoachAthleteLink]:
        return [link for link in self._by_id.values() if link.coach_id == coach_id]

    def list_by_athlete(self, athlete_id: UserId) -> list[CoachAthleteLink]:
        return [link for link in self._by_id.values() if link.athlete_id == athlete_id]

    def count_by_coach(self, coach_id: UserId) -> int:
        return len(self.list_by_coach(coach_id))


class InMemoryAthleteProfileRepository:
    """Simple in-memory AthleteProfileRepository for tests."""

    def __init__(self) -> None:
        self._by_athlete_id: dict[UserId, AthleteProfile] = {}

    def save(self, profile: AthleteProfile) -> AthleteProfile:
        self._by_athlete_id[profile.athlete_id] = profile
        return profile

    def get_by_athlete_id(self, athlete_id: UserId) -> AthleteProfile | None:
        return self._by_athlete_id.get(athlete_id)


class InMemoryPersonalRecordRepository:
    """Simple in-memory PersonalRecordRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[PersonalRecordId, PersonalRecord] = {}

    def save(self, record: PersonalRecord) -> PersonalRecord:
        self._by_id[record.id] = record
        return record

    def get_by_id(self, record_id: PersonalRecordId) -> PersonalRecord | None:
        return self._by_id.get(record_id)

    def delete(self, record_id: PersonalRecordId) -> None:
        self._by_id.pop(record_id, None)

    def list_by_athlete(self, athlete_id: UserId) -> list[PersonalRecord]:
        return [record for record in self._by_id.values() if record.athlete_id == athlete_id]

    def list_by_athlete_and_type(
        self,
        athlete_id: UserId,
        record_type: RecordType,
    ) -> list[PersonalRecord]:
        return [
            record
            for record in self._by_id.values()
            if record.athlete_id == athlete_id and record.record_type is record_type
        ]

    def list_by_athlete_page(
        self,
        athlete_id: UserId,
        *,
        offset: int,
        limit: int,
    ) -> list[PersonalRecord]:
        items = sorted(
            self.list_by_athlete(athlete_id),
            key=lambda record: record.achieved_at,
            reverse=True,
        )
        return items[offset : offset + limit]

    def count_by_athlete(self, athlete_id: UserId) -> int:
        return len(self.list_by_athlete(athlete_id))


class InMemoryWorkoutFeedbackRepository:
    """Simple in-memory WorkoutFeedbackRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[WorkoutFeedbackId, WorkoutFeedback] = {}

    def save(self, feedback: WorkoutFeedback) -> WorkoutFeedback:
        self._by_id[feedback.id] = feedback
        return feedback

    def get_by_id(self, feedback_id: WorkoutFeedbackId) -> WorkoutFeedback | None:
        return self._by_id.get(feedback_id)

    def list_by_athlete(self, athlete_id: UserId) -> list[WorkoutFeedback]:
        return [feedback for feedback in self._by_id.values() if feedback.athlete_id == athlete_id]

    def list_by_athlete_page(
        self,
        athlete_id: UserId,
        *,
        offset: int,
        limit: int,
    ) -> list[WorkoutFeedback]:
        items = sorted(
            self.list_by_athlete(athlete_id),
            key=lambda feedback: feedback.created_at,
            reverse=True,
        )
        return items[offset : offset + limit]

    def count_by_athlete(self, athlete_id: UserId) -> int:
        return len(self.list_by_athlete(athlete_id))
