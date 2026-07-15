from typing import Protocol

from domain.entities.workout_exercise import WorkoutExercise
from domain.value_objects.workout_cycle_id import WorkoutCycleId
from domain.value_objects.workout_exercise_id import WorkoutExerciseId


class WorkoutExerciseRepository(Protocol):
    """Persistence contract for workout exercises."""

    def save(self, exercise: WorkoutExercise) -> WorkoutExercise:
        """Persist a workout exercise."""

    def get_by_id(self, exercise_id: WorkoutExerciseId) -> WorkoutExercise | None:
        """Load workout exercise by identifier."""

    def list_by_cycle(self, cycle_id: WorkoutCycleId) -> list[WorkoutExercise]:
        """Return exercises for a cycle ordered by sort_order."""

    def delete_by_cycle(self, cycle_id: WorkoutCycleId) -> None:
        """Delete all exercises for a cycle."""
