from domain.entities.planned_workout import PlannedWorkout
from domain.repositories.workout_cycle_repository import WorkoutCycleRepository
from domain.repositories.workout_exercise_repository import WorkoutExerciseRepository


def format_workout_context(
    workout: PlannedWorkout,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
) -> str:
    lines = [
        f"Date: {workout.planned_date.isoformat()}",
        f"Type: {workout.workout_type.value}",
    ]
    if workout.title:
        lines.append(f"Title: {workout.title}")
    cycles = cycle_repository.list_by_workout(workout.id)
    for cycle in cycles:
        lines.append(f"Cycle: {cycle.name}")
        for exercise in exercise_repository.list_by_cycle(cycle.id):
            lines.append(f"  - {exercise.name}: {exercise.details}")
    return "\n".join(lines)
