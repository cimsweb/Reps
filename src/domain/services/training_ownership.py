"""Training data ownership rules for coach-athlete pairs."""

from domain.entities.planned_workout import PlannedWorkout
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.exceptions import TrainingAccessDeniedError
from domain.value_objects.user_id import UserId


def assert_training_plan_matches_pair(
    coach_id: UserId,
    athlete_id: UserId,
    plan: TrainingPlan,
) -> None:
    """Verify the plan belongs to the coach-athlete pair."""
    if plan.coach_id != coach_id or plan.athlete_id != athlete_id:
        raise TrainingAccessDeniedError("Training plan does not belong to coach-athlete pair")


def assert_planned_workout_belongs_to_pair(
    coach_id: UserId,
    athlete_id: UserId,
    workout: PlannedWorkout,
) -> None:
    """Verify the workout belongs to the coach-athlete pair."""
    if workout.coach_id != coach_id or workout.athlete_id != athlete_id:
        raise TrainingAccessDeniedError("Planned workout does not belong to coach-athlete pair")


def assert_planned_workout_matches_plan(workout: PlannedWorkout, plan: TrainingPlan) -> None:
    """Verify the workout is part of the training plan."""
    if workout.plan_id != plan.id:
        raise TrainingAccessDeniedError("Planned workout does not belong to training plan")
    if workout.coach_id != plan.coach_id or workout.athlete_id != plan.athlete_id:
        raise TrainingAccessDeniedError("Planned workout pair does not match training plan")


def assert_report_matches_workout(
    report: WorkoutCompletionReport,
    workout: PlannedWorkout,
) -> None:
    """Verify the report references the workout and athlete."""
    if report.planned_workout_id != workout.id:
        raise TrainingAccessDeniedError("Report must reference the planned workout")
    if report.athlete_id != workout.athlete_id:
        raise TrainingAccessDeniedError("Report athlete must match planned workout athlete")
