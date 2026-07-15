from dataclasses import dataclass

from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.workout_cycle_id import WorkoutCycleId


@dataclass(frozen=True, slots=True)
class WorkoutCycle:
    """Named cycle inside a planned workout (warm-up, main set, etc.)."""

    id: WorkoutCycleId
    planned_workout_id: PlannedWorkoutId
    name: str
    sort_order: int
