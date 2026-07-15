from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class WorkoutExerciseInput:
    """Exercise payload for plan creation or update."""

    name: str
    details: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class WorkoutCycleInput:
    """Cycle payload for plan creation or update."""

    name: str
    sort_order: int
    exercises: tuple[WorkoutExerciseInput, ...]


@dataclass(frozen=True, slots=True)
class PlannedWorkoutInput:
    """Planned workout payload for plan creation or update."""

    planned_date: date
    workout_type: str
    title: str | None
    cycles: tuple[WorkoutCycleInput, ...]
