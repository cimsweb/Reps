"""Integration tests for MVP 2 training data ingestion."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
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
    CreateDayTrainingPlanUseCase,
    CreateWeekTrainingPlanUseCase,
    SubmitWorkoutCompletionReportUseCase,
)
from domain.entities.plan_scope import PlanScope
from domain.entities.role import Role
from domain.entities.workout_type import WorkoutType
from domain.exceptions import TrainingAccessDeniedError
from infrastructure.db.coaching_repositories import (
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
)
from infrastructure.db.engine import get_database_url
from infrastructure.db.models import (
    PlannedWorkoutRecord,
    TrainingPlanRecord,
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


def _run_workout_input(planned_date: date) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type="run",
        title="Morning run",
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


@pytest.mark.integration
def test_training_ingestion_flow_persists_to_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()
    planned_date = _future_date()

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
        workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
        cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
        exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
        report_repository = SqlAlchemyWorkoutCompletionReportRepository(db_session)
        access_guard = TrainingAccessGuard(link_repository)

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

        AcceptInvitationUseCase(invitation_repository, link_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.commit()

        day_plan = CreateDayTrainingPlanUseCase(
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
            [_run_workout_input(planned_date)],
        )
        db_session.commit()

        plan_row = db_session.get(TrainingPlanRecord, day_plan.id.value)
        assert plan_row is not None
        assert plan_row.scope is PlanScope.DAY

        workout_row = db_session.scalar(
            select(PlannedWorkoutRecord).where(PlannedWorkoutRecord.plan_id == day_plan.id.value)
        )
        assert workout_row is not None
        assert workout_row.workout_type is WorkoutType.RUN

        cycle_row = db_session.scalar(
            select(WorkoutCycleRecord).where(
                WorkoutCycleRecord.planned_workout_id == workout_row.id
            )
        )
        assert cycle_row is not None
        assert cycle_row.name == "Main set"

        exercise_row = db_session.scalar(
            select(WorkoutExerciseRecord).where(WorkoutExerciseRecord.cycle_id == cycle_row.id)
        )
        assert exercise_row is not None
        assert exercise_row.details == "5 km"

        week_start = planned_date + timedelta(days=1)
        week_plan = CreateWeekTrainingPlanUseCase(
            plan_repository,
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(
            coach.id,
            Role.COACH,
            athlete.id,
            week_start,
            [
                _run_workout_input(week_start),
            ],
        )
        db_session.commit()

        week_plan_row = db_session.get(TrainingPlanRecord, week_plan.id.value)
        assert week_plan_row is not None
        assert week_plan_row.scope is PlanScope.WEEK

        report = SubmitWorkoutCompletionReportUseCase(
            workout_repository,
            report_repository,
            access_guard,
        ).execute(athlete.id, Role.ATHLETE, str(workout_row.id), 7, 8, "Solid effort")
        db_session.commit()

        report_row = db_session.get(WorkoutCompletionReportRecord, report.id.value)
        assert report_row is not None
        assert report_row.difficulty_rating == 7
        assert report_row.mood_rating == 8
        assert report_row.comment == "Solid effort"


@pytest.mark.integration
def test_create_training_plan_rejects_duplicate_date_in_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()
    planned_date = _future_date(10)

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
        workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
        cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
        exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
        access_guard = TrainingAccessGuard(link_repository)

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

        AcceptInvitationUseCase(invitation_repository, link_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.commit()

        create_use_case = CreateDayTrainingPlanUseCase(
            plan_repository,
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        )
        create_use_case.execute(
            coach.id,
            Role.COACH,
            athlete.id,
            planned_date,
            [_run_workout_input(planned_date)],
        )
        db_session.commit()

        second_plan = create_use_case.execute(
            coach.id,
            Role.COACH,
            athlete.id,
            planned_date,
            [_run_workout_input(planned_date)],
        )
        db_session.commit()

        workout_count = db_session.scalar(
            select(func.count())
            .select_from(PlannedWorkoutRecord)
            .where(
                PlannedWorkoutRecord.athlete_id == athlete.id,
                PlannedWorkoutRecord.planned_date == planned_date,
            )
        )
        assert workout_count == 1
        assert second_plan.id is not None


@pytest.mark.integration
def test_submit_report_rejects_unlinked_athlete_in_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    coach_email = f"coach-{uuid4()}@example.com"
    athlete_email = f"athlete-{uuid4()}@example.com"
    other_athlete_email = f"other-{uuid4()}@example.com"
    engine = create_engine(get_database_url())
    hasher = ScryptPasswordHasher()
    planned_date = _future_date(14)

    with OrmSession(engine) as db_session:
        user_repository = SqlAlchemyUserRepository(db_session)
        invitation_repository = SqlAlchemyInvitationRepository(db_session)
        link_repository = SqlAlchemyCoachAthleteLinkRepository(db_session)
        plan_repository = SqlAlchemyTrainingPlanRepository(db_session)
        workout_repository = SqlAlchemyPlannedWorkoutRepository(db_session)
        cycle_repository = SqlAlchemyWorkoutCycleRepository(db_session)
        exercise_repository = SqlAlchemyWorkoutExerciseRepository(db_session)
        report_repository = SqlAlchemyWorkoutCompletionReportRepository(db_session)
        access_guard = TrainingAccessGuard(link_repository)

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
        other_athlete = RegisterUserUseCase(user_repository, hasher).execute(
            other_athlete_email,
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

        AcceptInvitationUseCase(invitation_repository, link_repository).execute(
            athlete.id,
            Role.ATHLETE,
            athlete_email,
            str(invitation.id),
        )
        db_session.commit()

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
            [_run_workout_input(planned_date)],
        )
        db_session.commit()

        workout_row = db_session.scalar(
            select(PlannedWorkoutRecord).where(PlannedWorkoutRecord.plan_id == plan.id.value)
        )
        assert workout_row is not None

        with pytest.raises(TrainingAccessDeniedError):
            SubmitWorkoutCompletionReportUseCase(
                workout_repository,
                report_repository,
                access_guard,
            ).execute(other_athlete.id, Role.ATHLETE, str(workout_row.id), 5, 5)
