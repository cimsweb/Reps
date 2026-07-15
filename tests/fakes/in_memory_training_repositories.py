"""In-memory training repository fakes for unit tests."""

from datetime import date, datetime

from domain.entities.planned_workout import PlannedWorkout
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.entities.workout_cycle import WorkoutCycle
from domain.entities.workout_exercise import WorkoutExercise
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_completion_report_id import WorkoutCompletionReportId
from domain.value_objects.workout_cycle_id import WorkoutCycleId
from domain.value_objects.workout_exercise_id import WorkoutExerciseId


class InMemoryTrainingPlanRepository:
    """Simple in-memory TrainingPlanRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[TrainingPlanId, TrainingPlan] = {}

    def save(self, plan: TrainingPlan) -> TrainingPlan:
        self._by_id[plan.id] = plan
        return plan

    def get_by_id(self, plan_id: TrainingPlanId) -> TrainingPlan | None:
        return self._by_id.get(plan_id)


class InMemoryPlannedWorkoutRepository:
    """Simple in-memory PlannedWorkoutRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[PlannedWorkoutId, PlannedWorkout] = {}

    def save(self, workout: PlannedWorkout) -> PlannedWorkout:
        self._by_id[workout.id] = workout
        return workout

    def get_by_id(self, workout_id: PlannedWorkoutId) -> PlannedWorkout | None:
        return self._by_id.get(workout_id)

    def delete(self, workout_id: PlannedWorkoutId) -> None:
        self._by_id.pop(workout_id, None)

    def list_by_plan(self, plan_id: TrainingPlanId) -> list[PlannedWorkout]:
        return [workout for workout in self._by_id.values() if workout.plan_id == plan_id]

    def list_by_athlete_and_date_range(
        self,
        athlete_id: UserId,
        *,
        start_date: date,
        end_date: date,
    ) -> list[PlannedWorkout]:
        return [
            workout
            for workout in self._by_id.values()
            if workout.athlete_id == athlete_id and start_date <= workout.planned_date <= end_date
        ]

    def list_by_coach_and_athlete_date_range(
        self,
        coach_id: UserId,
        athlete_id: UserId,
        *,
        start_date: date,
        end_date: date,
    ) -> list[PlannedWorkout]:
        return [
            workout
            for workout in self._by_id.values()
            if workout.coach_id == coach_id
            and workout.athlete_id == athlete_id
            and start_date <= workout.planned_date <= end_date
        ]

    def get_by_athlete_and_date(
        self,
        athlete_id: UserId,
        planned_date: date,
    ) -> PlannedWorkout | None:
        for workout in self._by_id.values():
            if workout.athlete_id == athlete_id and workout.planned_date == planned_date:
                return workout
        return None


class InMemoryWorkoutCycleRepository:
    """Simple in-memory WorkoutCycleRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[WorkoutCycleId, WorkoutCycle] = {}

    def save(self, cycle: WorkoutCycle) -> WorkoutCycle:
        self._by_id[cycle.id] = cycle
        return cycle

    def get_by_id(self, cycle_id: WorkoutCycleId) -> WorkoutCycle | None:
        return self._by_id.get(cycle_id)

    def list_by_workout(self, workout_id: PlannedWorkoutId) -> list[WorkoutCycle]:
        return sorted(
            [cycle for cycle in self._by_id.values() if cycle.planned_workout_id == workout_id],
            key=lambda cycle: cycle.sort_order,
        )

    def delete_by_workout(self, workout_id: PlannedWorkoutId) -> None:
        to_delete = [
            cycle_id
            for cycle_id, cycle in self._by_id.items()
            if cycle.planned_workout_id == workout_id
        ]
        for cycle_id in to_delete:
            self._by_id.pop(cycle_id)


class InMemoryWorkoutExerciseRepository:
    """Simple in-memory WorkoutExerciseRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[WorkoutExerciseId, WorkoutExercise] = {}

    def save(self, exercise: WorkoutExercise) -> WorkoutExercise:
        self._by_id[exercise.id] = exercise
        return exercise

    def get_by_id(self, exercise_id: WorkoutExerciseId) -> WorkoutExercise | None:
        return self._by_id.get(exercise_id)

    def list_by_cycle(self, cycle_id: WorkoutCycleId) -> list[WorkoutExercise]:
        return sorted(
            [exercise for exercise in self._by_id.values() if exercise.cycle_id == cycle_id],
            key=lambda exercise: exercise.sort_order,
        )

    def delete_by_cycle(self, cycle_id: WorkoutCycleId) -> None:
        to_delete = [
            exercise_id
            for exercise_id, exercise in self._by_id.items()
            if exercise.cycle_id == cycle_id
        ]
        for exercise_id in to_delete:
            self._by_id.pop(exercise_id)


class InMemoryWorkoutCompletionReportRepository:
    """Simple in-memory WorkoutCompletionReportRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[WorkoutCompletionReportId, WorkoutCompletionReport] = {}
        self._by_workout: dict[PlannedWorkoutId, WorkoutCompletionReport] = {}

    def save(self, report: WorkoutCompletionReport) -> WorkoutCompletionReport:
        self._by_id[report.id] = report
        self._by_workout[report.planned_workout_id] = report
        return report

    def get_by_id(self, report_id: WorkoutCompletionReportId) -> WorkoutCompletionReport | None:
        return self._by_id.get(report_id)

    def get_by_planned_workout(
        self,
        planned_workout_id: PlannedWorkoutId,
    ) -> WorkoutCompletionReport | None:
        return self._by_workout.get(planned_workout_id)

    def list_by_athlete_and_date_range(
        self,
        athlete_id: UserId,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WorkoutCompletionReport]:
        return [
            report
            for report in self._by_id.values()
            if report.athlete_id == athlete_id and start_at <= report.created_at <= end_at
        ]
