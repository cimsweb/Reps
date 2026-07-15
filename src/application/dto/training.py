from dataclasses import dataclass
from datetime import date, datetime

from domain.entities.planned_workout import PlannedWorkout
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.entities.workout_cycle import WorkoutCycle
from domain.entities.workout_exercise import WorkoutExercise


@dataclass(frozen=True, slots=True)
class WorkoutExerciseView:
    """Workout exercise data for API responses."""

    id: str
    name: str
    details: str
    sort_order: int

    @classmethod
    def from_exercise(cls, exercise: WorkoutExercise) -> "WorkoutExerciseView":
        return cls(
            id=str(exercise.id.value),
            name=exercise.name,
            details=exercise.details,
            sort_order=exercise.sort_order,
        )


@dataclass(frozen=True, slots=True)
class WorkoutCycleView:
    """Workout cycle data for API responses."""

    id: str
    name: str
    sort_order: int
    exercises: tuple[WorkoutExerciseView, ...]

    @classmethod
    def from_cycle(
        cls,
        cycle: WorkoutCycle,
        exercises: tuple[WorkoutExerciseView, ...],
    ) -> "WorkoutCycleView":
        return cls(
            id=str(cycle.id.value),
            name=cycle.name,
            sort_order=cycle.sort_order,
            exercises=exercises,
        )


@dataclass(frozen=True, slots=True)
class PlannedWorkoutView:
    """Planned workout data for API responses."""

    id: str
    plan_id: str
    coach_id: str
    athlete_id: str
    planned_date: date
    workout_type: str
    title: str | None
    created_at: datetime
    cycles: tuple[WorkoutCycleView, ...] = ()

    @classmethod
    def from_workout(
        cls,
        workout: PlannedWorkout,
        cycles: tuple[WorkoutCycleView, ...],
    ) -> "PlannedWorkoutView":
        return cls(
            id=str(workout.id.value),
            plan_id=str(workout.plan_id.value),
            coach_id=str(workout.coach_id.value),
            athlete_id=str(workout.athlete_id.value),
            planned_date=workout.planned_date,
            workout_type=workout.workout_type.value,
            title=workout.title,
            created_at=workout.created_at,
            cycles=cycles,
        )


@dataclass(frozen=True, slots=True)
class TrainingPlanView:
    """Training plan data for API responses."""

    id: str
    coach_id: str
    athlete_id: str
    scope: str
    start_date: date
    created_at: datetime
    raw_text: str | None = None
    workouts: tuple[PlannedWorkoutView, ...] = ()

    @classmethod
    def from_plan(
        cls,
        plan: TrainingPlan,
        workouts: tuple[PlannedWorkoutView, ...],
    ) -> "TrainingPlanView":
        return cls(
            id=str(plan.id.value),
            coach_id=str(plan.coach_id.value),
            athlete_id=str(plan.athlete_id.value),
            scope=plan.scope.value,
            start_date=plan.start_date,
            created_at=plan.created_at,
            raw_text=plan.raw_text,
            workouts=workouts,
        )


@dataclass(frozen=True, slots=True)
class WorkoutCompletionReportView:
    """Workout completion report for API responses."""

    id: str
    planned_workout_id: str
    athlete_id: str
    difficulty_rating: int
    mood_rating: int
    comment: str | None
    created_at: datetime
    garmin_url: str | None = None
    raw_report_text: str | None = None

    @classmethod
    def from_report(cls, report: WorkoutCompletionReport) -> "WorkoutCompletionReportView":
        return cls(
            id=str(report.id.value),
            planned_workout_id=str(report.planned_workout_id.value),
            athlete_id=str(report.athlete_id.value),
            difficulty_rating=report.difficulty_rating.value,
            mood_rating=report.mood_rating.value,
            comment=report.comment,
            garmin_url=report.garmin_url,
            raw_report_text=report.raw_report_text,
            created_at=report.created_at,
        )


@dataclass(frozen=True, slots=True)
class TrainingCalendarView:
    """Planned workouts grouped for calendar display."""

    anchor_date: date
    period: str
    workouts: tuple[PlannedWorkoutView, ...]


@dataclass(frozen=True, slots=True)
class WorkoutReportSummaryView:
    """Completion reports grouped for period display."""

    anchor_date: date
    period: str
    reports: tuple[WorkoutCompletionReportView, ...]
