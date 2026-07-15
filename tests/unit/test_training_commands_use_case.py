"""Tests for MVP 2 training command use cases."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch
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
    CreateWeekTrainingPlanUseCase,
    DeletePlannedWorkoutUseCase,
    SubmitWorkoutCompletionReportUseCase,
    UpdatePlannedWorkoutUseCase,
)
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.plan_scope import PlanScope
from domain.entities.planned_workout import PlannedWorkout
from domain.entities.role import Role
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_type import WorkoutType
from domain.exceptions import (
    AuthorizationError,
    InvalidDifficultyRatingError,
    InvalidMoodRatingError,
    InvalidTrainingPlanError,
    InvalidWorkoutStructureError,
    PastWorkoutModificationError,
    PlannedWorkoutNotFoundError,
    TrainingAccessDeniedError,
    WorkoutReportAlreadyExistsError,
)
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
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


def _run_workout_input(
    planned_date: date,
    *,
    workout_type: str = "run",
    title: str | None = "Morning run",
) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type=workout_type,
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


def _training_repositories() -> tuple[
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


def _create_day_plan(
    coach_id: UserId,
    athlete_id: UserId,
    planned_date: date,
    workouts: list[PlannedWorkoutInput] | None = None,
) -> tuple[
    InMemoryPlannedWorkoutRepository,
    InMemoryWorkoutCycleRepository,
    InMemoryWorkoutExerciseRepository,
    TrainingPlan,
]:
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()
    use_case = CreateDayTrainingPlanUseCase(
        plans,
        workouts_repo,
        cycles,
        exercises,
        _linked_guard(coach_id, athlete_id),
    )
    plan = use_case.execute(
        coach_id,
        Role.COACH,
        athlete_id,
        planned_date,
        workouts or [_run_workout_input(planned_date)],
    )
    return workouts_repo, cycles, exercises, plan


def test_create_day_training_plan_for_linked_athlete() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()

    workouts_repo, _, _, plan = _create_day_plan(coach_id, athlete_id, planned_date)

    assert plan.scope is PlanScope.DAY
    assert plan.start_date == planned_date
    saved_workouts = workouts_repo.list_by_plan(plan.id)
    assert len(saved_workouts) == 1
    assert saved_workouts[0].workout_type is WorkoutType.RUN


def test_create_week_training_plan_with_multiple_workout_types() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    start_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()
    week_workouts = [
        _run_workout_input(start_date, workout_type="run"),
        _run_workout_input(start_date + timedelta(days=2), workout_type="bike", title="Ride"),
        _run_workout_input(start_date + timedelta(days=4), workout_type="gym", title="Strength"),
    ]

    plan = CreateWeekTrainingPlanUseCase(
        plans,
        workouts_repo,
        cycles,
        exercises,
        _linked_guard(coach_id, athlete_id),
    ).execute(coach_id, Role.COACH, athlete_id, start_date, week_workouts)

    assert plan.scope is PlanScope.WEEK
    saved_workouts = workouts_repo.list_by_plan(plan.id)
    assert len(saved_workouts) == 3
    assert {workout.workout_type for workout in saved_workouts} == {
        WorkoutType.RUN,
        WorkoutType.BIKE,
        WorkoutType.GYM,
    }


def test_create_training_plan_persists_cycles_and_exercises() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, cycles_repo, exercises_repo, plan = _create_day_plan(
        coach_id,
        athlete_id,
        planned_date,
    )

    workout = workouts_repo.list_by_plan(plan.id)[0]
    saved_cycles = cycles_repo.list_by_workout(workout.id)
    assert len(saved_cycles) == 1
    assert saved_cycles[0].name == "Main set"

    saved_exercises = exercises_repo.list_by_cycle(saved_cycles[0].id)
    assert len(saved_exercises) == 1
    assert saved_exercises[0].name == "Easy jog"
    assert saved_exercises[0].details == "5 km"


def test_submit_workout_completion_report_saves_ratings() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, _, _, plan = _create_day_plan(coach_id, athlete_id, planned_date)
    workout = workouts_repo.list_by_plan(plan.id)[0]
    _, _, _, _, reports = _training_repositories()

    report = SubmitWorkoutCompletionReportUseCase(
        workouts_repo,
        reports,
        _linked_guard(coach_id, athlete_id),
    ).execute(athlete_id, Role.ATHLETE, str(workout.id), 8, 9, " Felt strong ")

    assert report.difficulty_rating.value == 8
    assert report.mood_rating.value == 9
    assert report.comment == "Felt strong"


def test_submit_workout_completion_report_rejects_invalid_ratings() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, _, _, plan = _create_day_plan(coach_id, athlete_id, planned_date)
    workout = workouts_repo.list_by_plan(plan.id)[0]
    use_case = SubmitWorkoutCompletionReportUseCase(
        workouts_repo,
        InMemoryWorkoutCompletionReportRepository(),
        _linked_guard(coach_id, athlete_id),
    )

    with pytest.raises(InvalidDifficultyRatingError):
        use_case.execute(athlete_id, Role.ATHLETE, str(workout.id), 11, 5)

    with pytest.raises(InvalidMoodRatingError):
        use_case.execute(athlete_id, Role.ATHLETE, str(workout.id), 5, -1)


def test_submit_workout_completion_report_rejects_other_athlete() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, _, _, plan = _create_day_plan(coach_id, athlete_id, planned_date)
    workout = workouts_repo.list_by_plan(plan.id)[0]

    with pytest.raises(TrainingAccessDeniedError):
        SubmitWorkoutCompletionReportUseCase(
            workouts_repo,
            InMemoryWorkoutCompletionReportRepository(),
            _linked_guard(coach_id, athlete_id),
        ).execute(UserId(uuid4()), Role.ATHLETE, str(workout.id), 5, 5)


def test_create_day_training_plan_upserts_existing_date_for_same_coach() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()
    guard = _linked_guard(coach_id, athlete_id)
    use_case = CreateDayTrainingPlanUseCase(
        plans,
        workouts_repo,
        cycles,
        exercises,
        guard,
    )
    first_plan = use_case.execute(
        coach_id,
        Role.COACH,
        athlete_id,
        planned_date,
        [_run_workout_input(planned_date)],
    )
    first_workout_id = workouts_repo.list_by_plan(first_plan.id)[0].id

    second_plan = use_case.execute(
        coach_id,
        Role.COACH,
        athlete_id,
        planned_date,
        [_run_workout_input(planned_date)],
    )
    workouts = workouts_repo.list_by_athlete_and_date_range(
        athlete_id,
        start_date=planned_date,
        end_date=planned_date,
    )

    assert len(workouts) == 1
    assert workouts[0].id == first_workout_id
    assert workouts[0].plan_id == second_plan.id


def test_submit_workout_completion_report_rejects_duplicate_report() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, _, _, plan = _create_day_plan(coach_id, athlete_id, planned_date)
    workout = workouts_repo.list_by_plan(plan.id)[0]
    reports = InMemoryWorkoutCompletionReportRepository()
    use_case = SubmitWorkoutCompletionReportUseCase(
        workouts_repo,
        reports,
        _linked_guard(coach_id, athlete_id),
    )
    use_case.execute(athlete_id, Role.ATHLETE, str(workout.id), 5, 5)

    with pytest.raises(WorkoutReportAlreadyExistsError):
        use_case.execute(athlete_id, Role.ATHLETE, str(workout.id), 6, 6)


def test_create_training_plan_rejects_unlinked_coach() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()

    with pytest.raises(TrainingAccessDeniedError):
        CreateDayTrainingPlanUseCase(
            plans,
            workouts_repo,
            cycles,
            exercises,
            TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(
            coach_id,
            Role.COACH,
            athlete_id,
            planned_date,
            [_run_workout_input(planned_date)],
        )


def test_create_training_plan_rejects_athlete_role() -> None:
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()

    with pytest.raises(AuthorizationError):
        CreateDayTrainingPlanUseCase(
            plans,
            workouts_repo,
            cycles,
            exercises,
            TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(
            athlete_id,
            Role.ATHLETE,
            athlete_id,
            planned_date,
            [_run_workout_input(planned_date)],
        )


def test_create_training_plan_rejects_invalid_structure() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()
    invalid_workout = PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type="run",
        title="Run",
        cycles=(),
    )

    with pytest.raises(InvalidWorkoutStructureError):
        CreateDayTrainingPlanUseCase(
            plans,
            workouts_repo,
            cycles,
            exercises,
            _linked_guard(coach_id, athlete_id),
        ).execute(coach_id, Role.COACH, athlete_id, planned_date, [invalid_workout])


def test_create_day_training_plan_rejects_mismatched_workout_date() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    start_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()

    with pytest.raises(InvalidTrainingPlanError):
        CreateDayTrainingPlanUseCase(
            plans,
            workouts_repo,
            cycles,
            exercises,
            _linked_guard(coach_id, athlete_id),
        ).execute(
            coach_id,
            Role.COACH,
            athlete_id,
            start_date,
            [_run_workout_input(start_date + timedelta(days=1))],
        )


def test_create_week_training_plan_rejects_out_of_range_date() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    start_date = _future_date()
    plans, workouts_repo, cycles, exercises, _ = _training_repositories()

    with pytest.raises(InvalidTrainingPlanError):
        CreateWeekTrainingPlanUseCase(
            plans,
            workouts_repo,
            cycles,
            exercises,
            _linked_guard(coach_id, athlete_id),
        ).execute(
            coach_id,
            Role.COACH,
            athlete_id,
            start_date,
            [_run_workout_input(start_date + timedelta(days=7))],
        )


def test_update_planned_workout_changes_structure() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, cycles_repo, exercises_repo, plan = _create_day_plan(
        coach_id,
        athlete_id,
        planned_date,
    )
    workout = workouts_repo.list_by_plan(plan.id)[0]
    updated_input = PlannedWorkoutInput(
        planned_date=planned_date,
        workout_type="bike",
        title="Updated ride",
        cycles=(
            WorkoutCycleInput(
                name="Intervals",
                sort_order=0,
                exercises=(
                    WorkoutExerciseInput(
                        name="Sprint",
                        details="6 x 30 sec",
                        sort_order=0,
                    ),
                ),
            ),
        ),
    )

    updated = UpdatePlannedWorkoutUseCase(
        workouts_repo,
        cycles_repo,
        exercises_repo,
        _linked_guard(coach_id, athlete_id),
    ).execute(coach_id, Role.COACH, str(workout.id), updated_input)

    assert updated.workout_type is WorkoutType.BIKE
    assert updated.title == "Updated ride"
    saved_cycles = cycles_repo.list_by_workout(workout.id)
    assert saved_cycles[0].name == "Intervals"
    assert exercises_repo.list_by_cycle(saved_cycles[0].id)[0].name == "Sprint"


def test_delete_planned_workout_removes_workout() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    planned_date = _future_date()
    workouts_repo, _, _, plan = _create_day_plan(coach_id, athlete_id, planned_date)
    workout = workouts_repo.list_by_plan(plan.id)[0]

    DeletePlannedWorkoutUseCase(
        workouts_repo,
        _linked_guard(coach_id, athlete_id),
    ).execute(coach_id, Role.COACH, str(workout.id))

    assert workouts_repo.get_by_id(workout.id) is None


def test_update_planned_workout_rejects_past_workout() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    past_date = date(2026, 1, 1)
    workouts_repo = InMemoryPlannedWorkoutRepository()
    cycles_repo = InMemoryWorkoutCycleRepository()
    exercises_repo = InMemoryWorkoutExerciseRepository()
    workout_id = PlannedWorkoutId(uuid4())
    workouts_repo.save(
        PlannedWorkout(
            id=workout_id,
            plan_id=TrainingPlanId(uuid4()),
            coach_id=coach_id,
            athlete_id=athlete_id,
            planned_date=past_date,
            workout_type=WorkoutType.RUN,
            title="Past run",
            created_at=datetime.now(UTC),
        )
    )

    with (
        patch(
            "application.use_cases.training_commands._today_utc",
            return_value=date(2026, 6, 26),
        ),
        pytest.raises(PastWorkoutModificationError),
    ):
        UpdatePlannedWorkoutUseCase(
            workouts_repo,
            cycles_repo,
            exercises_repo,
            _linked_guard(coach_id, athlete_id),
        ).execute(
            coach_id,
            Role.COACH,
            str(workout_id),
            _run_workout_input(past_date),
        )


def test_delete_planned_workout_rejects_missing_workout() -> None:
    with pytest.raises(PlannedWorkoutNotFoundError):
        DeletePlannedWorkoutUseCase(
            InMemoryPlannedWorkoutRepository(),
            TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(UserId(uuid4()), Role.COACH, str(uuid4()))
