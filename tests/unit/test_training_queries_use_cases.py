"""Tests for MVP 2 training query use cases."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from application.dto.training_inputs import (
    PlannedWorkoutInput,
    WorkoutCycleInput,
    WorkoutExerciseInput,
)
from application.security.training_access_guard import TrainingAccessGuard
from application.use_cases.training_commands import (
    CreateDayTrainingPlanUseCase,
    SubmitWorkoutCompletionReportUseCase,
)
from application.use_cases.training_queries import (
    GetTrainingPlanForMonthUseCase,
    GetTrainingPlanForWeekUseCase,
    ListWorkoutReportsForMonthUseCase,
    ListWorkoutReportsForWeekUseCase,
)
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, TrainingAccessDeniedError
from domain.services.training_periods import PLAN_PERIOD_MONTH, PLAN_PERIOD_WEEK
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryCoachAthleteLinkRepository
from fakes.in_memory_training_repositories import (
    InMemoryPlannedWorkoutRepository,
    InMemoryTrainingPlanRepository,
    InMemoryWorkoutCompletionReportRepository,
    InMemoryWorkoutCycleRepository,
    InMemoryWorkoutExerciseRepository,
)


def _future_date(days_ahead: int = 7) -> date:
    return datetime.now(UTC).date() + timedelta(days=days_ahead)


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


def _linked_guard(coach_id: UserId, athlete_id: UserId) -> TrainingAccessGuard:
    links = InMemoryCoachAthleteLinkRepository()
    links.save(
        CoachAthleteLink(
            id=CoachAthleteLinkId(uuid4()),
            coach_id=coach_id,
            athlete_id=athlete_id,
            created_at=datetime.now(UTC),
        )
    )
    return TrainingAccessGuard(links)


def _repos() -> tuple[
    InMemoryTrainingPlanRepository,
    InMemoryPlannedWorkoutRepository,
    InMemoryWorkoutCycleRepository,
    InMemoryWorkoutExerciseRepository,
    InMemoryWorkoutCompletionReportRepository,
]:
    return (
        InMemoryTrainingPlanRepository(),
        InMemoryPlannedWorkoutRepository(),
        InMemoryWorkoutCycleRepository(),
        InMemoryWorkoutExerciseRepository(),
        InMemoryWorkoutCompletionReportRepository(),
    )


def test_get_training_plan_for_week_returns_linked_workouts() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    anchor = _future_date()
    plans, workout_repo, cycle_repo, exercise_repo, _ = _repos()
    guard = _linked_guard(coach_id, athlete_id)
    CreateDayTrainingPlanUseCase(
        plans,
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(coach_id, Role.COACH, athlete_id, anchor, [_workout_input(anchor)])

    calendar = GetTrainingPlanForWeekUseCase(
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(coach_id, Role.COACH, athlete_id, anchor)

    assert calendar.period == PLAN_PERIOD_WEEK
    assert len(calendar.workouts) == 1
    assert calendar.workouts[0].cycles[0].exercises[0].name == "Jog"


def test_get_training_plan_for_month_filters_by_calendar_month() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    anchor = date(2026, 8, 15)
    plans, workout_repo, cycle_repo, exercise_repo, _ = _repos()
    guard = _linked_guard(coach_id, athlete_id)
    august_first = date(2026, 8, 1)
    CreateDayTrainingPlanUseCase(
        plans,
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(coach_id, Role.COACH, athlete_id, august_first, [_workout_input(august_first)])
    CreateDayTrainingPlanUseCase(
        plans,
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(
        coach_id,
        Role.COACH,
        athlete_id,
        date(2026, 9, 1),
        [_workout_input(date(2026, 9, 1))],
    )

    calendar = GetTrainingPlanForMonthUseCase(
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(coach_id, Role.COACH, athlete_id, anchor)

    assert calendar.period == PLAN_PERIOD_MONTH
    assert len(calendar.workouts) == 1
    assert calendar.workouts[0].planned_date == date(2026, 8, 1)


def test_athlete_can_view_own_training_plan() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    anchor = _future_date(10)
    plans, workout_repo, cycle_repo, exercise_repo, _ = _repos()
    guard = _linked_guard(coach_id, athlete_id)
    CreateDayTrainingPlanUseCase(
        plans,
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(coach_id, Role.COACH, athlete_id, anchor, [_workout_input(anchor)])

    calendar = GetTrainingPlanForWeekUseCase(
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(athlete_id, Role.ATHLETE, athlete_id, anchor)

    assert len(calendar.workouts) == 1


def test_coach_cannot_view_unlinked_athlete_plan() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        GetTrainingPlanForWeekUseCase(
            InMemoryPlannedWorkoutRepository(),
            InMemoryWorkoutCycleRepository(),
            InMemoryWorkoutExerciseRepository(),
            TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(UserId(uuid4()), Role.COACH, UserId(uuid4()), _future_date())


def test_list_workout_reports_for_week_returns_reports() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    anchor = datetime.now(UTC).date()
    plans, workout_repo, cycle_repo, exercise_repo, reports = _repos()
    guard = _linked_guard(coach_id, athlete_id)
    plan = CreateDayTrainingPlanUseCase(
        plans,
        workout_repo,
        cycle_repo,
        exercise_repo,
        guard,
    ).execute(coach_id, Role.COACH, athlete_id, anchor, [_workout_input(anchor)])
    workout = workout_repo.list_by_plan(plan.id)[0]
    SubmitWorkoutCompletionReportUseCase(workout_repo, reports, guard).execute(
        athlete_id,
        Role.ATHLETE,
        str(workout.id),
        7,
        8,
        "Good",
    )

    summary = ListWorkoutReportsForWeekUseCase(reports, guard).execute(
        coach_id,
        Role.COACH,
        athlete_id,
        anchor,
    )

    assert len(summary.reports) == 1
    assert summary.reports[0].difficulty_rating == 7


def test_list_workout_reports_rejects_other_athlete() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        ListWorkoutReportsForMonthUseCase(
            InMemoryWorkoutCompletionReportRepository(),
            TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(UserId(uuid4()), Role.ATHLETE, UserId(uuid4()), _future_date())


def test_get_training_plan_rejects_admin_role() -> None:
    with pytest.raises(AuthorizationError):
        GetTrainingPlanForWeekUseCase(
            InMemoryPlannedWorkoutRepository(),
            InMemoryWorkoutCycleRepository(),
            InMemoryWorkoutExerciseRepository(),
            TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(UserId(uuid4()), Role.ADMIN, UserId(uuid4()), _future_date())
