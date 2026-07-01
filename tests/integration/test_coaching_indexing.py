"""Integration tests for coaching indexing and data integrity."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session as OrmSession

from application.security.coaching_access_guard import CoachingAccessGuard
from application.use_cases.accept_invitation import AcceptInvitationUseCase
from application.use_cases.decline_invitation import DeclineInvitationUseCase
from application.use_cases.personal_record_commands import CreatePersonalRecordUseCase
from application.use_cases.register_user import RegisterUserUseCase
from application.use_cases.send_invitation import SendInvitationUseCase
from application.use_cases.submit_workout_feedback import SubmitWorkoutFeedbackUseCase
from domain.entities.invitation_status import InvitationStatus
from domain.entities.record_type import RecordType
from domain.entities.role import Role
from domain.exceptions import CoachAthleteAccessDeniedError
from infrastructure.db.coaching_repositories import (
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
    SqlAlchemyPersonalRecordRepository,
    SqlAlchemyWorkoutFeedbackRepository,
)
from infrastructure.db.engine import create_db_engine
from infrastructure.db.models import CoachAthleteLinkRecord, InvitationRecord
from infrastructure.db.repositories import SqlAlchemyUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from integration.conftest import database_is_available


def _register_coach_and_athlete(
    user_repository: SqlAlchemyUserRepository,
    hasher: ScryptPasswordHasher,
) -> tuple[object, object, str, str]:
    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
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
    return coach, athlete, coach_email, athlete_email


@pytest.mark.integration
def test_accept_invitation_is_atomic_on_commit() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        coach, athlete, _, athlete_email = _register_coach_and_athlete(user_repository, hasher)

        invitation = SendInvitationUseCase(
            invitation_repository,
            link_repository,
            user_repository,
        ).execute(coach.id, Role.COACH, athlete_email)

        AcceptInvitationUseCase(invitation_repository, link_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.commit()

        invitation_row = db_session.get(InvitationRecord, invitation.id.value)
        link_count = db_session.scalar(
            select(CoachAthleteLinkRecord).where(
                CoachAthleteLinkRecord.coach_id == coach.id.value,
                CoachAthleteLinkRecord.athlete_id == athlete.id.value,
            )
        )

        assert invitation_row is not None
        assert invitation_row.status is InvitationStatus.ACCEPTED
        assert link_count is not None


@pytest.mark.integration
def test_accept_invitation_rolls_back_without_commit() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        coach, athlete, _, athlete_email = _register_coach_and_athlete(user_repository, hasher)
        db_session.commit()

        invitation = SendInvitationUseCase(
            invitation_repository,
            link_repository,
            user_repository,
        ).execute(coach.id, Role.COACH, athlete_email)

        AcceptInvitationUseCase(invitation_repository, link_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.rollback()

        invitation_row = db_session.get(InvitationRecord, invitation.id.value)
        link_row = db_session.scalar(
            select(CoachAthleteLinkRecord).where(
                CoachAthleteLinkRecord.coach_id == coach.id.value,
                CoachAthleteLinkRecord.athlete_id == athlete.id.value,
            )
        )

        assert invitation_row is None or invitation_row.status is InvitationStatus.PENDING
        assert link_row is None


@pytest.mark.integration
def test_decline_invitation_does_not_create_link() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        coach, athlete, _, athlete_email = _register_coach_and_athlete(user_repository, hasher)

        invitation = SendInvitationUseCase(
            invitation_repository,
            link_repository,
            user_repository,
        ).execute(coach.id, Role.COACH, athlete_email)

        DeclineInvitationUseCase(invitation_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.commit()

        link_row = db_session.scalar(
            select(CoachAthleteLinkRecord).where(
                CoachAthleteLinkRecord.athlete_id == athlete.id.value,
            )
        )
        assert link_row is None


@pytest.mark.integration
def test_athlete_can_have_multiple_coaches() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        athlete_email = f"athlete-{uuid4()}@example.com"
        athlete = RegisterUserUseCase(user_repository, hasher).execute(
            athlete_email,
            "secure1A",
            Role.ATHLETE,
        )

        coach_ids: list[object] = []
        for _ in range(2):
            coach_email = f"coach-{uuid4()}@example.com"
            coach = RegisterUserUseCase(user_repository, hasher).execute(
                coach_email,
                "secure1A",
                Role.COACH,
            )
            coach_ids.append(coach.id)
            invitation = SendInvitationUseCase(
                invitation_repository,
                link_repository,
                user_repository,
            ).execute(coach.id, Role.COACH, athlete_email)
            AcceptInvitationUseCase(invitation_repository, link_repository).execute(
                athlete.id,
                Role.ATHLETE,
                athlete_email,
                str(invitation.id),
            )

        db_session.commit()
        links = link_repository.list_by_athlete(athlete.id)
        assert len(links) == 2
        assert link_repository.count_by_coach(coach_ids[0]) == 1
        assert link_repository.count_by_coach(coach_ids[1]) == 1


@pytest.mark.integration
def test_coach_cannot_access_unlinked_athlete() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        coach, athlete, _, _ = _register_coach_and_athlete(user_repository, hasher)
        db_session.commit()

        with pytest.raises(CoachAthleteAccessDeniedError):
            CoachingAccessGuard(link_repository).ensure_coach_can_access_athlete(
                coach.id,
                athlete.id,
            )


@pytest.mark.integration
def test_list_by_coach_uses_single_query() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    query_count = {"value": 0}

    def _count_queries(*_: object) -> None:
        query_count["value"] += 1

    event.listen(engine, "before_cursor_execute", _count_queries)

    try:
        with OrmSession(engine) as db_session:
            user_repository = SqlAlchemyUserRepository(db_session)
            link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
            invitation_repository = SqlAlchemyInvitationRepository(db_session)
            coach, athlete, _, athlete_email = _register_coach_and_athlete(
                user_repository,
                hasher,
            )
            invitation = SendInvitationUseCase(
                invitation_repository,
                link_repository,
                user_repository,
            ).execute(coach.id, Role.COACH, athlete_email)
            AcceptInvitationUseCase(invitation_repository, link_repository).execute(
                athlete.id,
                Role.ATHLETE,
                athlete_email,
                str(invitation.id),
            )
            db_session.commit()

            query_count["value"] = 0
            links = link_repository.list_by_coach(coach.id)
            assert len(links) == 1
            assert query_count["value"] == 1
    finally:
        event.remove(engine, "before_cursor_execute", _count_queries)


@pytest.mark.integration
def test_repository_filters_support_grouping_queries() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        athlete = RegisterUserUseCase(user_repository, hasher).execute(
            f"athlete-{uuid4()}@example.com",
            "secure1A",
            Role.ATHLETE,
        )
        record_repository = SqlAlchemyPersonalRecordRepository(db_session)
        feedback_repository = SqlAlchemyWorkoutFeedbackRepository(db_session)

        CreatePersonalRecordUseCase(record_repository).execute(
            athlete.id,
            Role.ATHLETE,
            "distance",
            "5K",
            "19:45",
            "time",
            datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        )
        CreatePersonalRecordUseCase(record_repository).execute(
            athlete.id,
            Role.ATHLETE,
            "exercise",
            "Pull-ups",
            "20",
            "reps",
            datetime(2026, 6, 2, 8, 0, tzinfo=UTC),
        )
        SubmitWorkoutFeedbackUseCase(feedback_repository).execute(
            athlete.id,
            Role.ATHLETE,
            "Good session",
        )
        db_session.commit()

        distance_records = record_repository.list_by_athlete_and_type(
            athlete.id,
            RecordType.DISTANCE,
        )
        feedback_page = feedback_repository.list_by_athlete_page(
            athlete.id,
            offset=0,
            limit=10,
        )

        assert len(distance_records) == 1
        assert distance_records[0].record_type is RecordType.DISTANCE
        assert len(feedback_page) == 1
