"""Integration tests for MVP 2.2 agent session indexing and repositories."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session as OrmSession

from application.dto.training_inputs import (
    PlannedWorkoutInput,
    WorkoutCycleInput,
    WorkoutExerciseInput,
)
from application.security.training_access_guard import TrainingAccessGuard
from application.use_cases.accept_invitation import AcceptInvitationUseCase
from application.use_cases.register_user import RegisterUserUseCase
from application.use_cases.send_invitation import SendInvitationUseCase
from application.use_cases.training_commands import CreateDayTrainingPlanUseCase
from domain.entities.agent_message import AgentMessage
from domain.entities.agent_message_role import AgentMessageRole
from domain.entities.agent_session import AgentSession
from domain.entities.agent_session_kind import AgentSessionKind
from domain.entities.agent_session_status import AgentSessionStatus
from domain.entities.role import Role
from domain.exceptions import DuplicateActiveReportAgentSessionError
from domain.value_objects.agent_message_id import AgentMessageId
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from infrastructure.db.agent_repositories import (
    SqlAlchemyAgentMessageRepository,
    SqlAlchemyAgentSessionRepository,
)
from infrastructure.db.coaching_repositories import (
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
)
from infrastructure.db.engine import create_db_engine
from infrastructure.db.repositories import SqlAlchemyUserRepository
from infrastructure.db.training_repositories import (
    SqlAlchemyPlannedWorkoutRepository,
    SqlAlchemyTrainingPlanRepository,
    SqlAlchemyWorkoutCycleRepository,
    SqlAlchemyWorkoutExerciseRepository,
)
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from integration.conftest import database_is_available


def _workout_input(planned_date: date) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type="run",
        title="Easy run",
        cycles=(
            WorkoutCycleInput(
                name="Main",
                sort_order=0,
                exercises=(WorkoutExerciseInput(name="Jog", details="5 km", sort_order=0),),
            ),
        ),
    )


def _link_coach_and_athlete(db_session: OrmSession) -> tuple:
    user_repository = SqlAlchemyUserRepository(db_session)
    hasher = ScryptPasswordHasher()
    coach = RegisterUserUseCase(user_repository, hasher).execute(
        f"coach-{uuid4()}@example.com",
        "secure1A",
        Role.COACH,
    )
    athlete = RegisterUserUseCase(user_repository, hasher).execute(
        f"athlete-{uuid4()}@example.com",
        "secure1A",
        Role.ATHLETE,
    )
    invitation_repository = SqlAlchemyInvitationRepository(db_session)
    link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
    invitation = SendInvitationUseCase(
        invitation_repository,
        link_repository,
        user_repository,
    ).execute(coach.id, Role.COACH, str(athlete.email))
    AcceptInvitationUseCase(invitation_repository, link_repository).execute(
        athlete.id,
        Role.ATHLETE,
        str(athlete.email),
        str(invitation.id),
    )
    db_session.commit()
    return coach, athlete


def _create_planned_workout(db_session: OrmSession, coach, athlete) -> PlannedWorkoutId:
    plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
    workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
    cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
    exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
    access_guard = TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db_session))
    planned_date = datetime.now(UTC).date()
    plan = CreateDayTrainingPlanUseCase(
        plan_repository,
        workout_repository,
        cycle_repository,
        exercise_repository,
        access_guard,
    ).execute(
        coach.id,
        Role.COACH,
        athlete.id,
        planned_date,
        [_workout_input(planned_date)],
    )
    db_session.commit()
    workouts = workout_repository.list_by_plan(plan.id)
    assert workouts
    return workouts[0].id


@pytest.mark.integration
def test_agent_session_repository_indexes_exist() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    inspector = inspect(engine)
    session_indexes = {index["name"] for index in inspector.get_indexes("agent_sessions")}
    message_indexes = {index["name"] for index in inspector.get_indexes("agent_messages")}

    assert "ix_agent_sessions_coach_id_status" in session_indexes
    assert "ix_agent_sessions_athlete_id_status" in session_indexes
    assert "uq_agent_sessions_active_report_per_workout" in session_indexes
    assert "ix_agent_messages_session_id_sort_order" in message_indexes


@pytest.mark.integration
def test_agent_message_history_preserves_sort_order() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    with OrmSession(engine) as db_session:
        coach, athlete = _link_coach_and_athlete(db_session)
        session_repository = SqlAlchemyAgentSessionRepository(db_session)
        message_repository = SqlAlchemyAgentMessageRepository(db_session)
        now = datetime.now(UTC)
        session = session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.PLAN_CREATION,
                coach_id=coach.id,
                athlete_id=athlete.id,
                planned_workout_id=None,
                status=AgentSessionStatus.ACTIVE,
                start_date=date.today(),
                created_at=now,
                updated_at=now,
            )
        )
        for index in range(3):
            message_repository.append(
                AgentMessage(
                    id=AgentMessageId(uuid4()),
                    session_id=session.id,
                    role=AgentMessageRole.USER if index % 2 == 0 else AgentMessageRole.ASSISTANT,
                    content=f"message-{index}",
                    metadata=None,
                    sort_order=index,
                    created_at=now,
                )
            )
        db_session.commit()
        messages = message_repository.list_by_session(session.id)
        assert [message.sort_order for message in messages] == [0, 1, 2]
        assert [message.content for message in messages] == ["message-0", "message-1", "message-2"]


@pytest.mark.integration
def test_unique_active_report_session_per_workout() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    with OrmSession(engine) as db_session:
        coach, athlete = _link_coach_and_athlete(db_session)
        workout_id = _create_planned_workout(db_session, coach, athlete)
        session_repository = SqlAlchemyAgentSessionRepository(db_session)
        now = datetime.now(UTC)

        session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.REPORT_ASSISTANCE,
                coach_id=None,
                athlete_id=athlete.id,
                planned_workout_id=workout_id,
                status=AgentSessionStatus.ACTIVE,
                start_date=None,
                created_at=now,
                updated_at=now,
            )
        )
        db_session.commit()

        with pytest.raises(DuplicateActiveReportAgentSessionError):
            session_repository.save(
                AgentSession(
                    id=AgentSessionId(uuid4()),
                    kind=AgentSessionKind.REPORT_ASSISTANCE,
                    coach_id=None,
                    athlete_id=athlete.id,
                    planned_workout_id=workout_id,
                    status=AgentSessionStatus.ACTIVE,
                    start_date=None,
                    created_at=now,
                    updated_at=now,
                )
            )
        db_session.rollback()


@pytest.mark.integration
def test_agent_session_complete_and_list_active() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    with OrmSession(engine) as db_session:
        coach, athlete = _link_coach_and_athlete(db_session)
        session_repository = SqlAlchemyAgentSessionRepository(db_session)
        now = datetime.now(UTC)
        session = session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.PLAN_CREATION,
                coach_id=coach.id,
                athlete_id=athlete.id,
                planned_workout_id=None,
                status=AgentSessionStatus.ACTIVE,
                start_date=date.today(),
                created_at=now,
                updated_at=now,
            )
        )
        db_session.commit()

        active = session_repository.list_active_by_coach(coach.id)
        assert len(active) == 1
        assert active[0].id == session.id

        completed = session_repository.complete(session.id)
        db_session.commit()
        assert completed.status is AgentSessionStatus.COMPLETED
        assert session_repository.list_active_by_coach(coach.id) == []


@pytest.mark.integration
def test_abandon_expired_active_sessions() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    with OrmSession(engine) as db_session:
        coach, athlete = _link_coach_and_athlete(db_session)
        session_repository = SqlAlchemyAgentSessionRepository(db_session)
        stale_time = datetime.now(UTC) - timedelta(hours=30)
        session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.PLAN_CREATION,
                coach_id=coach.id,
                athlete_id=athlete.id,
                planned_workout_id=None,
                status=AgentSessionStatus.ACTIVE,
                start_date=date.today(),
                created_at=stale_time,
                updated_at=stale_time,
            )
        )
        db_session.commit()

        updated_count = session_repository.abandon_expired_active_sessions()
        db_session.commit()
        assert updated_count == 1
        assert session_repository.list_active_by_coach(coach.id) == []


@pytest.mark.integration
def test_user_delete_cascades_agent_sessions() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    with OrmSession(engine) as db_session:
        coach, athlete = _link_coach_and_athlete(db_session)
        session_repository = SqlAlchemyAgentSessionRepository(db_session)
        message_repository = SqlAlchemyAgentMessageRepository(db_session)
        now = datetime.now(UTC)
        session = session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.PLAN_CREATION,
                coach_id=coach.id,
                athlete_id=athlete.id,
                planned_workout_id=None,
                status=AgentSessionStatus.ACTIVE,
                start_date=date.today(),
                created_at=now,
                updated_at=now,
            )
        )
        message_repository.append(
            AgentMessage(
                id=AgentMessageId(uuid4()),
                session_id=session.id,
                role=AgentMessageRole.USER,
                content="hello",
                metadata=None,
                sort_order=0,
                created_at=now,
            )
        )
        db_session.commit()
        athlete_user_id = athlete.id.value

        db_session.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": athlete_user_id},
        )
        db_session.commit()

        assert session_repository.get_by_id(session.id) is None
