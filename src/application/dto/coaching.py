from dataclasses import dataclass
from datetime import datetime

from domain.entities.athlete_profile import AthleteProfile
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.invitation import Invitation
from domain.entities.personal_record import PersonalRecord
from domain.entities.workout_feedback import WorkoutFeedback


@dataclass(frozen=True, slots=True)
class InvitationView:
    """Invitation data for API responses."""

    id: str
    coach_id: str
    athlete_email: str
    status: str
    created_at: datetime
    responded_at: datetime | None

    @classmethod
    def from_invitation(cls, invitation: Invitation) -> "InvitationView":
        return cls(
            id=str(invitation.id.value),
            coach_id=str(invitation.coach_id.value),
            athlete_email=str(invitation.athlete_email),
            status=invitation.status.value,
            created_at=invitation.created_at,
            responded_at=invitation.responded_at,
        )


@dataclass(frozen=True, slots=True)
class CoachAthleteView:
    """Coach-athlete link data for API responses."""

    id: str
    coach_id: str
    athlete_id: str
    created_at: datetime

    @classmethod
    def from_link(cls, link: CoachAthleteLink) -> "CoachAthleteView":
        return cls(
            id=str(link.id.value),
            coach_id=str(link.coach_id.value),
            athlete_id=str(link.athlete_id.value),
            created_at=link.created_at,
        )


@dataclass(frozen=True, slots=True)
class AthleteProfileView:
    """Athlete profile data for API responses."""

    athlete_id: str
    height_cm: int
    weight_kg: int
    age: int
    gender: str
    updated_at: datetime

    @classmethod
    def from_profile(cls, profile: AthleteProfile) -> "AthleteProfileView":
        return cls(
            athlete_id=str(profile.athlete_id.value),
            height_cm=profile.height_cm.value,
            weight_kg=profile.weight_kg.value,
            age=profile.age.value,
            gender=profile.gender.value,
            updated_at=profile.updated_at,
        )


@dataclass(frozen=True, slots=True)
class PersonalRecordView:
    """Personal record data for API responses."""

    id: str
    athlete_id: str
    record_type: str
    name: str
    value: str
    unit: str
    achieved_at: datetime
    created_at: datetime

    @classmethod
    def from_record(cls, record: PersonalRecord) -> "PersonalRecordView":
        return cls(
            id=str(record.id.value),
            athlete_id=str(record.athlete_id.value),
            record_type=record.record_type.value,
            name=record.name,
            value=str(record.value),
            unit=str(record.unit),
            achieved_at=record.achieved_at,
            created_at=record.created_at,
        )


@dataclass(frozen=True, slots=True)
class WorkoutFeedbackView:
    """Workout feedback data for API responses."""

    id: str
    athlete_id: str
    text: str
    created_at: datetime

    @classmethod
    def from_feedback(cls, feedback: WorkoutFeedback) -> "WorkoutFeedbackView":
        return cls(
            id=str(feedback.id.value),
            athlete_id=str(feedback.athlete_id.value),
            text=feedback.text,
            created_at=feedback.created_at,
        )


@dataclass(frozen=True, slots=True)
class PaginatedPersonalRecords:
    """Paginated list of personal records."""

    items: tuple[PersonalRecordView, ...]
    total: int


@dataclass(frozen=True, slots=True)
class PaginatedWorkoutFeedback:
    """Paginated list of workout feedback entries."""

    items: tuple[WorkoutFeedbackView, ...]
    total: int
