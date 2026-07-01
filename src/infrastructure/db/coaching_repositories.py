from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain.entities.athlete_profile import AthleteProfile
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.invitation import Invitation
from domain.entities.invitation_status import InvitationStatus
from domain.entities.personal_record import PersonalRecord
from domain.entities.record_type import RecordType
from domain.entities.workout_feedback import WorkoutFeedback
from domain.value_objects.age import Age
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.email import Email
from domain.value_objects.garmin_report_url import GarminReportUrl
from domain.value_objects.height_cm import HeightCm
from domain.value_objects.invitation_id import InvitationId
from domain.value_objects.personal_record_id import PersonalRecordId
from domain.value_objects.record_unit import RecordUnit
from domain.value_objects.record_value import RecordValue
from domain.value_objects.user_id import UserId
from domain.value_objects.weight_kg import WeightKg
from domain.value_objects.workout_feedback_id import WorkoutFeedbackId
from infrastructure.db.models import (
    AthleteProfileRecord,
    CoachAthleteLinkRecord,
    InvitationRecord,
    PersonalRecordRecord,
    WorkoutFeedbackRecord,
)


def _to_domain_invitation(record: InvitationRecord) -> Invitation:
    return Invitation(
        id=InvitationId(record.id),
        coach_id=UserId(record.coach_id),
        athlete_email=Email(record.athlete_email),
        status=record.status,
        created_at=record.created_at,
        responded_at=record.responded_at,
    )


def _to_domain_link(record: CoachAthleteLinkRecord) -> CoachAthleteLink:
    return CoachAthleteLink(
        id=CoachAthleteLinkId(record.id),
        coach_id=UserId(record.coach_id),
        athlete_id=UserId(record.athlete_id),
        created_at=record.created_at,
    )


def _to_domain_profile(record: AthleteProfileRecord) -> AthleteProfile:
    return AthleteProfile(
        athlete_id=UserId(record.athlete_id),
        height_cm=HeightCm(record.height_cm),
        weight_kg=WeightKg(record.weight_kg),
        age=Age(record.age),
        gender=record.gender,
        updated_at=record.updated_at,
    )


def _to_domain_personal_record(record: PersonalRecordRecord) -> PersonalRecord:
    return PersonalRecord(
        id=PersonalRecordId(record.id),
        athlete_id=UserId(record.athlete_id),
        record_type=record.record_type,
        name=record.name,
        value=RecordValue(record.value),
        unit=RecordUnit(record.unit),
        achieved_at=record.achieved_at,
        created_at=record.created_at,
    )


def _to_domain_feedback(record: WorkoutFeedbackRecord) -> WorkoutFeedback:
    garmin_url = GarminReportUrl(record.garmin_url) if record.garmin_url else None
    return WorkoutFeedback(
        id=WorkoutFeedbackId(record.id),
        athlete_id=UserId(record.athlete_id),
        text=record.text,
        garmin_url=garmin_url,
        created_at=record.created_at,
    )


class SqlAlchemyInvitationRepository:
    """SQLAlchemy implementation of InvitationRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, invitation: Invitation) -> Invitation:
        record = self._db_session.get(InvitationRecord, invitation.id.value)
        if record is None:
            record = InvitationRecord(
                id=invitation.id.value,
                coach_id=invitation.coach_id.value,
                athlete_email=str(invitation.athlete_email),
                status=invitation.status,
                created_at=invitation.created_at,
                responded_at=invitation.responded_at,
            )
            self._db_session.add(record)
        else:
            record.coach_id = invitation.coach_id.value
            record.athlete_email = str(invitation.athlete_email)
            record.status = invitation.status
            record.created_at = invitation.created_at
            record.responded_at = invitation.responded_at

        self._db_session.flush()
        return _to_domain_invitation(record)

    def get_by_id(self, invitation_id: InvitationId) -> Invitation | None:
        record = self._db_session.get(InvitationRecord, invitation_id.value)
        return _to_domain_invitation(record) if record else None

    def get_pending_by_coach_and_email(
        self,
        coach_id: UserId,
        athlete_email: Email,
    ) -> Invitation | None:
        stmt = select(InvitationRecord).where(
            InvitationRecord.coach_id == coach_id.value,
            InvitationRecord.athlete_email == str(athlete_email),
            InvitationRecord.status == InvitationStatus.PENDING,
        )
        record = self._db_session.scalar(stmt)
        return _to_domain_invitation(record) if record else None

    def list_by_coach(self, coach_id: UserId) -> list[Invitation]:
        stmt = (
            select(InvitationRecord)
            .where(InvitationRecord.coach_id == coach_id.value)
            .order_by(InvitationRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_invitation(record) for record in records]

    def list_by_coach_and_status(
        self,
        coach_id: UserId,
        status: InvitationStatus,
    ) -> list[Invitation]:
        stmt = (
            select(InvitationRecord)
            .where(
                InvitationRecord.coach_id == coach_id.value,
                InvitationRecord.status == status,
            )
            .order_by(InvitationRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_invitation(record) for record in records]

    def list_pending_for_email(self, athlete_email: Email) -> list[Invitation]:
        stmt = (
            select(InvitationRecord)
            .where(
                InvitationRecord.athlete_email == str(athlete_email),
                InvitationRecord.status == InvitationStatus.PENDING,
            )
            .order_by(InvitationRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_invitation(record) for record in records]


class SqlAlchemyCoachAthleteLinkRepository:
    """SQLAlchemy implementation of CoachAthleteLinkRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, link: CoachAthleteLink) -> CoachAthleteLink:
        record = self._db_session.get(CoachAthleteLinkRecord, link.id.value)
        if record is None:
            record = CoachAthleteLinkRecord(
                id=link.id.value,
                coach_id=link.coach_id.value,
                athlete_id=link.athlete_id.value,
                created_at=link.created_at,
            )
            self._db_session.add(record)
        else:
            record.coach_id = link.coach_id.value
            record.athlete_id = link.athlete_id.value
            record.created_at = link.created_at

        self._db_session.flush()
        return _to_domain_link(record)

    def exists(self, coach_id: UserId, athlete_id: UserId) -> bool:
        stmt = select(CoachAthleteLinkRecord.id).where(
            CoachAthleteLinkRecord.coach_id == coach_id.value,
            CoachAthleteLinkRecord.athlete_id == athlete_id.value,
        )
        return self._db_session.scalar(stmt) is not None

    def get_by_coach_and_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> CoachAthleteLink | None:
        stmt = select(CoachAthleteLinkRecord).where(
            CoachAthleteLinkRecord.coach_id == coach_id.value,
            CoachAthleteLinkRecord.athlete_id == athlete_id.value,
        )
        record = self._db_session.scalar(stmt)
        return _to_domain_link(record) if record else None

    def list_by_coach(self, coach_id: UserId) -> list[CoachAthleteLink]:
        stmt = (
            select(CoachAthleteLinkRecord)
            .where(CoachAthleteLinkRecord.coach_id == coach_id.value)
            .order_by(CoachAthleteLinkRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_link(record) for record in records]

    def list_by_athlete(self, athlete_id: UserId) -> list[CoachAthleteLink]:
        stmt = (
            select(CoachAthleteLinkRecord)
            .where(CoachAthleteLinkRecord.athlete_id == athlete_id.value)
            .order_by(CoachAthleteLinkRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_link(record) for record in records]

    def count_by_coach(self, coach_id: UserId) -> int:
        stmt = (
            select(func.count())
            .select_from(CoachAthleteLinkRecord)
            .where(CoachAthleteLinkRecord.coach_id == coach_id.value)
        )
        return int(self._db_session.scalar(stmt) or 0)


class SqlAlchemyAthleteProfileRepository:
    """SQLAlchemy implementation of AthleteProfileRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, profile: AthleteProfile) -> AthleteProfile:
        record = self._db_session.get(AthleteProfileRecord, profile.athlete_id.value)
        if record is None:
            record = AthleteProfileRecord(
                athlete_id=profile.athlete_id.value,
                height_cm=profile.height_cm.value,
                weight_kg=profile.weight_kg.value,
                age=profile.age.value,
                gender=profile.gender,
                updated_at=profile.updated_at,
            )
            self._db_session.add(record)
        else:
            record.height_cm = profile.height_cm.value
            record.weight_kg = profile.weight_kg.value
            record.age = profile.age.value
            record.gender = profile.gender
            record.updated_at = profile.updated_at

        self._db_session.flush()
        return _to_domain_profile(record)

    def get_by_athlete_id(self, athlete_id: UserId) -> AthleteProfile | None:
        record = self._db_session.get(AthleteProfileRecord, athlete_id.value)
        return _to_domain_profile(record) if record else None


class SqlAlchemyPersonalRecordRepository:
    """SQLAlchemy implementation of PersonalRecordRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, record_domain: PersonalRecord) -> PersonalRecord:
        record = self._db_session.get(PersonalRecordRecord, record_domain.id.value)
        if record is None:
            record = PersonalRecordRecord(
                id=record_domain.id.value,
                athlete_id=record_domain.athlete_id.value,
                record_type=record_domain.record_type,
                name=record_domain.name,
                value=str(record_domain.value),
                unit=str(record_domain.unit),
                achieved_at=record_domain.achieved_at,
                created_at=record_domain.created_at,
            )
            self._db_session.add(record)
        else:
            record.athlete_id = record_domain.athlete_id.value
            record.record_type = record_domain.record_type
            record.name = record_domain.name
            record.value = str(record_domain.value)
            record.unit = str(record_domain.unit)
            record.achieved_at = record_domain.achieved_at
            record.created_at = record_domain.created_at

        self._db_session.flush()
        return _to_domain_personal_record(record)

    def get_by_id(self, record_id: PersonalRecordId) -> PersonalRecord | None:
        record = self._db_session.get(PersonalRecordRecord, record_id.value)
        return _to_domain_personal_record(record) if record else None

    def delete(self, record_id: PersonalRecordId) -> None:
        record = self._db_session.get(PersonalRecordRecord, record_id.value)
        if record is not None:
            self._db_session.delete(record)
            self._db_session.flush()

    def list_by_athlete(self, athlete_id: UserId) -> list[PersonalRecord]:
        stmt = (
            select(PersonalRecordRecord)
            .where(PersonalRecordRecord.athlete_id == athlete_id.value)
            .order_by(PersonalRecordRecord.achieved_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_personal_record(record) for record in records]

    def list_by_athlete_and_type(
        self,
        athlete_id: UserId,
        record_type: RecordType,
    ) -> list[PersonalRecord]:
        stmt = (
            select(PersonalRecordRecord)
            .where(
                PersonalRecordRecord.athlete_id == athlete_id.value,
                PersonalRecordRecord.record_type == record_type,
            )
            .order_by(PersonalRecordRecord.achieved_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_personal_record(record) for record in records]

    def list_by_athlete_page(
        self,
        athlete_id: UserId,
        *,
        offset: int,
        limit: int,
    ) -> list[PersonalRecord]:
        stmt = (
            select(PersonalRecordRecord)
            .where(PersonalRecordRecord.athlete_id == athlete_id.value)
            .order_by(PersonalRecordRecord.achieved_at.desc())
            .offset(offset)
            .limit(limit)
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_personal_record(record) for record in records]

    def count_by_athlete(self, athlete_id: UserId) -> int:
        stmt = (
            select(func.count())
            .select_from(PersonalRecordRecord)
            .where(PersonalRecordRecord.athlete_id == athlete_id.value)
        )
        return int(self._db_session.scalar(stmt) or 0)


class SqlAlchemyWorkoutFeedbackRepository:
    """SQLAlchemy implementation of WorkoutFeedbackRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, feedback: WorkoutFeedback) -> WorkoutFeedback:
        record = self._db_session.get(WorkoutFeedbackRecord, feedback.id.value)
        garmin_url = str(feedback.garmin_url) if feedback.garmin_url else None
        if record is None:
            record = WorkoutFeedbackRecord(
                id=feedback.id.value,
                athlete_id=feedback.athlete_id.value,
                text=feedback.text,
                garmin_url=garmin_url,
                created_at=feedback.created_at,
            )
            self._db_session.add(record)
        else:
            record.athlete_id = feedback.athlete_id.value
            record.text = feedback.text
            record.garmin_url = garmin_url
            record.created_at = feedback.created_at

        self._db_session.flush()
        return _to_domain_feedback(record)

    def get_by_id(self, feedback_id: WorkoutFeedbackId) -> WorkoutFeedback | None:
        record = self._db_session.get(WorkoutFeedbackRecord, feedback_id.value)
        return _to_domain_feedback(record) if record else None

    def list_by_athlete(self, athlete_id: UserId) -> list[WorkoutFeedback]:
        stmt = (
            select(WorkoutFeedbackRecord)
            .where(WorkoutFeedbackRecord.athlete_id == athlete_id.value)
            .order_by(WorkoutFeedbackRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_feedback(record) for record in records]

    def list_by_athlete_page(
        self,
        athlete_id: UserId,
        *,
        offset: int,
        limit: int,
    ) -> list[WorkoutFeedback]:
        stmt = (
            select(WorkoutFeedbackRecord)
            .where(WorkoutFeedbackRecord.athlete_id == athlete_id.value)
            .order_by(WorkoutFeedbackRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_feedback(record) for record in records]

    def count_by_athlete(self, athlete_id: UserId) -> int:
        stmt = (
            select(func.count())
            .select_from(WorkoutFeedbackRecord)
            .where(WorkoutFeedbackRecord.athlete_id == athlete_id.value)
        )
        return int(self._db_session.scalar(stmt) or 0)
