"""Integration tests for MVP 2 training indexing and data integrity."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
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
from application.use_cases.training_commands import (
    CreateWeekTrainingPlanUseCase,
    SubmitWorkoutCompletionReportUseCase,
)
from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import TrainingAccessDeniedError
from infrastructure.db.coaching_repositories import (
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
)
from infrastructure.db.engine import create_db_engine
from infrastructure.db.models import (
    PlannedWorkoutRecord,
    TrainingPlanRecord,
    UserRecord,
    WorkoutCompletionReportRecord,
    WorkoutCycleRecord,
    WorkoutExerciseRecord,
)
from infrastructure.db.repositories import SqlAlchemyUserRepository
from infrastructure.db.training_repositories import (
    SqlAlchemyPlannedWorkoutRepository,
    SqlAlchemyTrainingPlanRepository,
    SqlAlchemyWorkoutCompletionReportRepository,
    SqlAlchemyWorkoutCycleRepository,
    SqlAlchemyWorkoutExerciseRepository,
)
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from integration.conftest import database_is_available


def _future_date(days_ahead: int = 7) -> date:
    return datetime.now(UTC).date() + timedelta(days=days_ahead)


def _workout_input(planned_date: date, *, title: str) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type="run",
        title=title,
        cycles=(
            WorkoutCycleInput(
                name="Main set",
                sort_order=0,
                exercises=(
                    WorkoutExerciseInput(
                        name="Easy jog",
                        details="5 km",
                        sort_order=0,
                    ),
                ),
            ),
        ),
    )


def _link_coach_and_athlete(
    db_session: OrmSession,
    user_repository: SqlAlchemyUserRepository,
    hasher: ScryptPasswordHasher,
) -> tuple[User, User]:
    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
    invitation_repository = SqlAlchemyInvitationRepository(db_session)
    link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)

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
    return coach, athlete


@pytest.mark.integration
def test_week_training_plan_commits_atomically() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    start_date = _future_date()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        coach, athlete = _link_coach_and_athlete(db_session, user_repository, hasher)
        plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
        workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
        cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
        exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
        access_guard = TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db_session))

        week_workouts = [
            _workout_input(start_date, title="Day 1"),
            _workout_input(start_date + timedelta(days=2), title="Day 3"),
            _workout_input(start_date + timedelta(days=4), title="Day 5"),
        ]
        plan = CreateWeekTrainingPlanUseCase(
            plan_repository,
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(coach.id, Role.COACH, athlete.id, start_date, week_workouts)
        db_session.commit()

        plan_row = db_session.get(TrainingPlanRecord, plan.id.value)
        workout_count = db_session.scalar(
            select(func.count())
            .select_from(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.plan_id == plan.id.value)
        )
        cycle_count = db_session.scalar(
            select(func.count())
            .select_from(WorkoutCycleRecord)
            .join(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.plan_id == plan.id.value)
        )
        exercise_count = db_session.scalar(
            select(func.count())
            .select_from(WorkoutExerciseRecord)
            .join(WorkoutCycleRecord)
            .join(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.plan_id == plan.id.value)
        )

        assert plan_row is not None
        assert workout_count == 3
        assert cycle_count == 3
        assert exercise_count == 3


@pytest.mark.integration
def test_week_training_plan_rolls_back_without_commit() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    start_date = _future_date(14)

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        coach, athlete = _link_coach_and_athlete(db_session, user_repository, hasher)
        db_session.commit()

        plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
        workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
        cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
        exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
        access_guard = TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db_session))

        plan = CreateWeekTrainingPlanUseCase(
            plan_repository,
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(
            coach.id,
            Role.COACH,
            athlete.id,
            start_date,
            [
                _workout_input(start_date, title="Day 1"),
                _workout_input(start_date + timedelta(days=1), title="Day 2"),
            ],
        )
        db_session.rollback()

        plan_count = db_session.scalar(
            select(func.count())
            .select_from(TrainingPlanRecord)
            .where(TrainingPlanRecord.id == plan.id.value)
        )
        workout_count = db_session.scalar(
            select(func.count())
            .select_from(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.athlete_id == athlete.id.value)
        )
        cycle_count = db_session.scalar(
            select(func.count())
            .select_from(WorkoutCycleRecord)
            .join(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.athlete_id == athlete.id.value)
        )
        exercise_count = db_session.scalar(
            select(func.count())
            .select_from(WorkoutExerciseRecord)
            .join(WorkoutCycleRecord)
            .join(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.athlete_id == athlete.id.value)
        )

        assert plan_count == 0
        assert workout_count == 0
        assert cycle_count == 0
        assert exercise_count == 0


@pytest.mark.integration
def test_deleting_athlete_cascades_training_data() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    start_date = _future_date(21)

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        coach, athlete = _link_coach_and_athlete(db_session, user_repository, hasher)
        plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
        workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
        cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
        exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
        report_repository = SqlAlchemyWorkoutCompletionReportRepository(db_session)
        access_guard = TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db_session))

        plan = CreateWeekTrainingPlanUseCase(
            plan_repository,
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(
            coach.id,
            Role.COACH,
            athlete.id,
            start_date,
            [_workout_input(start_date, title="Day 1")],
        )
        workout_row = db_session.scalar(
            select(PlannedWorkoutRecord).where(PlannedWorkoutRecord.plan_id == plan.id.value)
        )
        assert workout_row is not None

        SubmitWorkoutCompletionReportUseCase(
            workout_repository,
            report_repository,
            access_guard,
        ).execute(athlete.id, Role.ATHLETE, str(workout_row.id), 6, 7)
        db_session.commit()

        athlete_record = db_session.get(UserRecord, athlete.id.value)
        assert athlete_record is not None
        db_session.delete(athlete_record)
        db_session.commit()

        assert (
            db_session.scalar(
                select(func.count())
                .select_from(TrainingPlanRecord)
                .where(TrainingPlanRecord.athlete_id == athlete.id.value)
            )
            == 0
        )
        assert (
            db_session.scalar(
                select(func.count())
                .select_from(PlannedWorkoutRecord)
                .where(PlannedWorkoutRecord.athlete_id == athlete.id.value)
            )
            == 0
        )
        assert (
            db_session.scalar(
                select(func.count())
                .select_from(WorkoutCompletionReportRecord)
                .where(WorkoutCompletionReportRecord.athlete_id == athlete.id.value)
            )
            == 0
        )


@pytest.mark.integration
def test_coach_cannot_view_unlinked_athlete_training() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        coach, athlete = _link_coach_and_athlete(db_session, user_repository, hasher)
        other_athlete = RegisterUserUseCase(user_repository, hasher).execute(
            f"other-{uuid4()}@example.com",
            "secure1A",
            Role.ATHLETE,
        )
        db_session.commit()

        with pytest.raises(TrainingAccessDeniedError):
            TrainingAccessGuard(
                SqlAlchemyCoachAthleteLinkRepository(db_session)
            ).ensure_coach_can_view_athlete_training(
                coach.id,
                other_athlete.id,
            )


@pytest.mark.integration
def test_list_by_coach_and_athlete_date_range_uses_single_query() -> None:
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
            coach, athlete = _link_coach_and_athlete(db_session, user_repository, hasher)
            plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
            workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
            cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
            exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
            access_guard = TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db_session))
            start_date = _future_date(28)

            CreateWeekTrainingPlanUseCase(
                plan_repository,
                workout_repository,
                cycle_repository,
                exercise_repository,
                access_guard,
            ).execute(
                coach.id,
                Role.COACH,
                athlete.id,
                start_date,
                [
                    _workout_input(start_date, title="Day 1"),
                    _workout_input(start_date + timedelta(days=3), title="Day 4"),
                ],
            )
            db_session.commit()

            query_count["value"] = 0
            workouts = workout_repository.list_by_coach_and_athlete_date_range(
                coach.id,
                athlete.id,
                start_date=start_date,
                end_date=start_date + timedelta(days=6),
            )

            assert len(workouts) == 2
            assert query_count["value"] == 1
    finally:
        event.remove(engine, "before_cursor_execute", _count_queries)
