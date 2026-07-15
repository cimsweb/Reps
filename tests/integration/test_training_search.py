"""Integration tests for MVP 2 training search use cases."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
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
from application.use_cases.training_queries import (
    GetTrainingPlanForMonthUseCase,
    GetTrainingPlanForWeekUseCase,
    ListWorkoutReportsForWeekUseCase,
)
from domain.entities.role import Role
from domain.services.training_periods import PLAN_PERIOD_MONTH, PLAN_PERIOD_WEEK
from infrastructure.db.coaching_repositories import (
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
)
from infrastructure.db.engine import create_db_engine
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


def _workout_input(planned_date: date) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type="run",
        title="Run",
        cycles=(
            WorkoutCycleInput(
                name="Main",
                sort_order=0,
                exercises=(
                    WorkoutExerciseInput(
                        name="Jog",
                        details="5 km",
                        sort_order=0,
                    ),
                ),
            ),
        ),
    )


@pytest.mark.integration
def test_training_search_returns_plan_and_reports_from_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    engine = create_db_engine()
    hasher = ScryptPasswordHasher()
    start_date = datetime.now(UTC).date() + timedelta(days=7)

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
            f"coach-{uuid4()}@example.com",
            "secure1A",
            Role.COACH,
        )
        athlete_email = f"athlete-{uuid4()}@example.com"
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
                _workout_input(start_date),
                _workout_input(start_date + timedelta(days=2)),
            ],
        )
        workout = workout_repository.list_by_plan(plan.id)[0]
        SubmitWorkoutCompletionReportUseCase(
            workout_repository,
            report_repository,
            access_guard,
        ).execute(athlete.id, Role.ATHLETE, str(workout.id), 6, 7)
        db_session.commit()

        week_plan = GetTrainingPlanForWeekUseCase(
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(coach.id, Role.COACH, athlete.id, start_date)
        assert week_plan.period == PLAN_PERIOD_WEEK
        assert len(week_plan.workouts) == 2

        month_plan = GetTrainingPlanForMonthUseCase(
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(athlete.id, Role.ATHLETE, athlete.id, start_date)
        assert month_plan.period == PLAN_PERIOD_MONTH
        assert len(month_plan.workouts) == 2

        reports = ListWorkoutReportsForWeekUseCase(report_repository, access_guard).execute(
            athlete.id,
            Role.ATHLETE,
            athlete.id,
            datetime.now(UTC).date(),
        )
        assert len(reports.reports) == 1
