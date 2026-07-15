from typing import Protocol

from domain.entities.workout_cycle import WorkoutCycle
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.workout_cycle_id import WorkoutCycleId


class WorkoutCycleRepository(Protocol):
    """Persistence contract for workout cycles."""

    def save(self, cycle: WorkoutCycle) -> WorkoutCycle:
        """Persist a workout cycle."""

    def get_by_id(self, cycle_id: WorkoutCycleId) -> WorkoutCycle | None:
        """Load workout cycle by identifier."""

    def list_by_workout(self, workout_id: PlannedWorkoutId) -> list[WorkoutCycle]:
        """Return cycles for a planned workout ordered by sort_order."""

    def delete_by_workout(self, workout_id: PlannedWorkoutId) -> None:
        """Delete all cycles for a planned workout."""
