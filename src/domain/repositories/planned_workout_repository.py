from datetime import date
from typing import Protocol

from domain.entities.planned_workout import PlannedWorkout
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId


class PlannedWorkoutRepository(Protocol):
    """Persistence contract for planned workouts."""

    def save(self, workout: PlannedWorkout) -> PlannedWorkout:
        """Persist a planned workout."""

    def get_by_id(self, workout_id: PlannedWorkoutId) -> PlannedWorkout | None:
        """Load planned workout by identifier."""

    def delete(self, workout_id: PlannedWorkoutId) -> None:
        """Delete a planned workout."""

    def list_by_plan(self, plan_id: TrainingPlanId) -> list[PlannedWorkout]:
        """Return all workouts belonging to a training plan."""

    def list_by_athlete_and_date_range(
        self,
        athlete_id: UserId,
        *,
        start_date: date,
        end_date: date,
    ) -> list[PlannedWorkout]:
        """Return athlete workouts within an inclusive date range."""

    def list_by_coach_and_athlete_date_range(
        self,
        coach_id: UserId,
        athlete_id: UserId,
        *,
        start_date: date,
        end_date: date,
    ) -> list[PlannedWorkout]:
        """Return workouts for a coach-athlete pair within an inclusive date range."""

    def get_by_athlete_and_date(
        self,
        athlete_id: UserId,
        planned_date: date,
    ) -> PlannedWorkout | None:
        """Return a workout scheduled for the athlete on a specific date."""
