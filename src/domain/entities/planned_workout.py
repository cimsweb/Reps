from dataclasses import dataclass
from datetime import date, datetime

from domain.entities.workout_type import WorkoutType
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class PlannedWorkout:
    """Single scheduled workout on a calendar date."""

    id: PlannedWorkoutId
    plan_id: TrainingPlanId
    coach_id: UserId
    athlete_id: UserId
    planned_date: date
    workout_type: WorkoutType
    title: str | None
    created_at: datetime
