"""Unit tests for training ownership rules."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from domain.entities.plan_scope import PlanScope
from domain.entities.planned_workout import PlannedWorkout
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.entities.workout_type import WorkoutType
from domain.exceptions import TrainingAccessDeniedError
from domain.services.training_ownership import (
    assert_planned_workout_belongs_to_pair,
    assert_planned_workout_matches_plan,
    assert_report_matches_workout,
    assert_training_plan_matches_pair,
)
from domain.value_objects.difficulty_rating import DifficultyRating
from domain.value_objects.mood_rating import MoodRating
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_completion_report_id import WorkoutCompletionReportId


def _plan(coach_id: UserId, athlete_id: UserId) -> TrainingPlan:
    return TrainingPlan(
        id=TrainingPlanId(uuid4()),
        coach_id=coach_id,
        athlete_id=athlete_id,
        scope=PlanScope.WEEK,
        start_date=date(2026, 7, 1),
        created_at=datetime.now(UTC),
    )


def _workout(plan: TrainingPlan, *, athlete_id: UserId | None = None) -> PlannedWorkout:
    return PlannedWorkout(
        id=PlannedWorkoutId(uuid4()),
        plan_id=plan.id,
        coach_id=plan.coach_id,
        athlete_id=athlete_id or plan.athlete_id,
        planned_date=date(2026, 7, 1),
        workout_type=WorkoutType.RUN,
        title="Run",
        created_at=datetime.now(UTC),
    )


def test_assert_training_plan_matches_pair_allows_matching_pair() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    plan = _plan(coach_id, athlete_id)
    assert_training_plan_matches_pair(coach_id, athlete_id, plan)


def test_assert_training_plan_matches_pair_rejects_mismatch() -> None:
    plan = _plan(UserId(uuid4()), UserId(uuid4()))
    with pytest.raises(TrainingAccessDeniedError):
        assert_training_plan_matches_pair(UserId(uuid4()), UserId(uuid4()), plan)


def test_assert_planned_workout_belongs_to_pair_allows_matching_pair() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    plan = _plan(coach_id, athlete_id)
    workout = _workout(plan)
    assert_planned_workout_belongs_to_pair(coach_id, athlete_id, workout)


def test_assert_planned_workout_belongs_to_pair_rejects_mismatch() -> None:
    plan = _plan(UserId(uuid4()), UserId(uuid4()))
    workout = _workout(plan)
    with pytest.raises(TrainingAccessDeniedError):
        assert_planned_workout_belongs_to_pair(UserId(uuid4()), UserId(uuid4()), workout)


def test_assert_planned_workout_matches_plan_allows_matching_plan() -> None:
    plan = _plan(UserId(uuid4()), UserId(uuid4()))
    workout = _workout(plan)
    assert_planned_workout_matches_plan(workout, plan)


def test_assert_planned_workout_matches_plan_rejects_other_plan() -> None:
    plan = _plan(UserId(uuid4()), UserId(uuid4()))
    other_plan = _plan(UserId(uuid4()), UserId(uuid4()))
    workout = PlannedWorkout(
        id=PlannedWorkoutId(uuid4()),
        plan_id=other_plan.id,
        coach_id=plan.coach_id,
        athlete_id=plan.athlete_id,
        planned_date=date(2026, 7, 1),
        workout_type=WorkoutType.RUN,
        title="Run",
        created_at=datetime.now(UTC),
    )
    with pytest.raises(TrainingAccessDeniedError):
        assert_planned_workout_matches_plan(workout, plan)


def test_assert_report_matches_workout_allows_matching_report() -> None:
    plan = _plan(UserId(uuid4()), UserId(uuid4()))
    workout = _workout(plan)
    report = WorkoutCompletionReport(
        id=WorkoutCompletionReportId(uuid4()),
        planned_workout_id=workout.id,
        athlete_id=workout.athlete_id,
        difficulty_rating=DifficultyRating(5),
        mood_rating=MoodRating(7),
        comment=None,
        created_at=datetime.now(UTC),
    )
    assert_report_matches_workout(report, workout)


def test_assert_report_matches_workout_rejects_other_athlete() -> None:
    plan = _plan(UserId(uuid4()), UserId(uuid4()))
    workout = _workout(plan)
    report = WorkoutCompletionReport(
        id=WorkoutCompletionReportId(uuid4()),
        planned_workout_id=workout.id,
        athlete_id=UserId(uuid4()),
        difficulty_rating=DifficultyRating(5),
        mood_rating=MoodRating(7),
        comment=None,
        created_at=datetime.now(UTC),
    )
    with pytest.raises(TrainingAccessDeniedError):
        assert_report_matches_workout(report, workout)
