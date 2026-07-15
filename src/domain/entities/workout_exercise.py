from dataclasses import dataclass

from domain.value_objects.workout_cycle_id import WorkoutCycleId
from domain.value_objects.workout_exercise_id import WorkoutExerciseId


@dataclass(frozen=True, slots=True)
class WorkoutExercise:
    """Exercise or interval entry inside a workout cycle."""

    id: WorkoutExerciseId
    cycle_id: WorkoutCycleId
    name: str
    details: str
    sort_order: int
