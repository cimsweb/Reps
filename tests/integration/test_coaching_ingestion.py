"""Integration tests for MVP 1 data ingestion."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session as OrmSession

from application.use_cases.accept_invitation import AcceptInvitationUseCase
from application.use_cases.personal_record_commands import (
    CreatePersonalRecordUseCase,
    DeletePersonalRecordUseCase,
)
from application.use_cases.register_user import RegisterUserUseCase
from application.use_cases.save_athlete_profile import SaveAthleteProfileUseCase
from application.use_cases.send_invitation import SendInvitationUseCase
from application.use_cases.submit_workout_feedback import SubmitWorkoutFeedbackUseCase
from domain.entities.invitation_status import InvitationStatus
from domain.entities.role import Role
from domain.exceptions import DuplicateInvitationError, InvalidGarminUrlError
from infrastructure.db.coaching_repositories import (
    SqlAlchemyAthleteProfileRepository,
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
    SqlAlchemyPersonalRecordRepository,
    SqlAlchemyWorkoutFeedbackRepository,
)
from infrastructure.db.engine import get_database_url
from infrastructure.db.models import (
    AthleteProfileRecord,
    CoachAthleteLinkRecord,
    InvitationRecord,
    PersonalRecordRecord,
    WorkoutFeedbackRecord,
)
from infrastructure.db.repositories import SqlAlchemyUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from integration.conftest import database_is_available


@pytest.mark.integration
def test_coaching_ingestion_flow_persists_to_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        profile_repository = SqlAlchemyAthleteProfileRepository(db_session)
        record_repository = SqlAlchemyPersonalRecordRepository(db_session)
        feedback_repository = SqlAlchemyWorkoutFeedbackRepository(db_session)

        coach = RegisterUserUseCase(user_repository, hasher).execute(
            coach_email,
            "secure1A",
            Role.COACH,
        )
        athlete = RegisterUserUseCase(user_repository, hasher).execute(
            athlete_email,
            "secure1A",
            Role.ATHLETE,
        )
        db_session.commit()

        invitation = SendInvitationUseCase(
            invitation_repository,
            link_repository,
            user_repository,
        ).execute(coach.id, Role.COACH, athlete_email)
        db_session.commit()

        invitation_record = db_session.scalar(
            select(InvitationRecord).where(InvitationRecord.id == invitation.id.value)
        )
        assert invitation_record is not None
        assert invitation_record.status is InvitationStatus.PENDING

        link = AcceptInvitationUseCase(invitation_repository, link_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.commit()

        link_record = db_session.scalar(
            select(CoachAthleteLinkRecord).where(CoachAthleteLinkRecord.id == link.id.value)
        )
        assert link_record is not None

        SaveAthleteProfileUseCase(profile_repository).execute(
            athlete.id,
            Role.ATHLETE,
            180,
            75,
            28,
            "male",
        )
        db_session.commit()

        profile_record = db_session.get(AthleteProfileRecord, athlete.id.value)
        assert profile_record is not None
        assert profile_record.height_cm == 180

        record = CreatePersonalRecordUseCase(record_repository).execute(
            athlete.id,
            Role.ATHLETE,
            "distance",
            "5K",
            "19:45",
            "time",
            datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        )
        db_session.commit()

        record_row = db_session.get(PersonalRecordRecord, record.id.value)
        assert record_row is not None

        feedback = SubmitWorkoutFeedbackUseCase(feedback_repository).execute(
            athlete.id,
            Role.ATHLETE,
            "Strong session",
            "https://connect.garmin.com/modern/activity/999",
        )
        db_session.commit()

        feedback_row = db_session.get(WorkoutFeedbackRecord, feedback.id.value)
        assert feedback_row is not None
        assert feedback_row.garmin_url is not None


@pytest.mark.integration
def test_send_invitation_rejects_duplicate_in_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)

        coach = RegisterUserUseCase(user_repository, hasher).execute(
            coach_email,
            "secure1A",
            Role.COACH,
        )
        db_session.commit()

        send_use_case = SendInvitationUseCase(
            invitation_repository,
            link_repository,
            user_repository,
        )
        send_use_case.execute(coach.id, Role.COACH, athlete_email)
        db_session.commit()

        with pytest.raises(DuplicateInvitationError):
            send_use_case.execute(coach.id, Role.COACH, athlete_email)


@pytest.mark.integration
def test_submit_feedback_rejects_invalid_garmin_url_in_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    athlete_email = f"athlete-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        athlete = RegisterUserUseCase(user_repository, hasher).execute(
            athlete_email,
            "secure1A",
            Role.ATHLETE,
        )
        db_session.commit()

        with pytest.raises(InvalidGarminUrlError):
            SubmitWorkoutFeedbackUseCase(SqlAlchemyWorkoutFeedbackRepository(db_session)).execute(
                athlete.id,
                Role.ATHLETE,
                "Feedback text",
                "https://example.com/not-garmin",
            )


@pytest.mark.integration
def test_delete_personal_record_persists_in_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    athlete_email = f"athlete-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        record_repository = SqlAlchemyPersonalRecordRepository(db_session)
        athlete = RegisterUserUseCase(user_repository, hasher).execute(
            athlete_email,
            "secure1A",
            Role.ATHLETE,
        )
        db_session.commit()

        record = CreatePersonalRecordUseCase(record_repository).execute(
            athlete.id,
            Role.ATHLETE,
            "exercise",
            "Pull-ups",
            "20",
            "reps",
            datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        )
        db_session.commit()

        DeletePersonalRecordUseCase(record_repository).execute(
            athlete.id,
            Role.ATHLETE,
            str(record.id),
        )
        db_session.commit()

        deleted = db_session.get(PersonalRecordRecord, record.id.value)
        assert deleted is None
