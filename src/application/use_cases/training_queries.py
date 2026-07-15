"""Use cases for MVP 2 training read operations."""

from collections.abc import Callable
from datetime import date, datetime

from application.dto.training import (
    PlannedWorkoutView,
    TrainingCalendarView,
    WorkoutCompletionReportView,
    WorkoutCycleView,
    WorkoutExerciseView,
    WorkoutReportSummaryView,
)
from application.security.training_access_guard import TrainingAccessGuard
from domain.entities.planned_workout import PlannedWorkout
from domain.entities.role import Role
from domain.exceptions import AuthorizationError
from domain.repositories.planned_workout_repository import PlannedWorkoutRepository
from domain.repositories.workout_completion_report_repository import (
    WorkoutCompletionReportRepository,
)
from domain.repositories.workout_cycle_repository import WorkoutCycleRepository
from domain.repositories.workout_exercise_repository import WorkoutExerciseRepository
from domain.services.training_periods import (
    PLAN_PERIOD_MONTH,
    PLAN_PERIOD_WEEK,
    REPORT_PERIOD_MONTH,
    REPORT_PERIOD_WEEK,
    plan_month_range,
    plan_week_range,
    report_month_range,
    report_week_range,
    resolve_anchor_date,
)
from domain.value_objects.user_id import UserId


class GetTrainingPlanForWeekUseCase:
    """Return planned workouts for a week starting at anchor_date."""

    def __init__(
        self,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
        anchor_date: date | None = None,
    ) -> TrainingCalendarView:
        return _get_training_calendar(
            actor_id=actor_id,
            actor_role=actor_role,
            athlete_id=athlete_id,
            anchor_date=anchor_date,
            period=PLAN_PERIOD_WEEK,
            date_range=plan_week_range,
            workout_repository=self._workout_repository,
            cycle_repository=self._cycle_repository,
            exercise_repository=self._exercise_repository,
            access_guard=self._access_guard,
        )


class GetTrainingPlanForMonthUseCase:
    """Return planned workouts for a month containing anchor_date."""

    def __init__(
        self,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
        anchor_date: date | None = None,
    ) -> TrainingCalendarView:
        return _get_training_calendar(
            actor_id=actor_id,
            actor_role=actor_role,
            athlete_id=athlete_id,
            anchor_date=anchor_date,
            period=PLAN_PERIOD_MONTH,
            date_range=plan_month_range,
            workout_repository=self._workout_repository,
            cycle_repository=self._cycle_repository,
            exercise_repository=self._exercise_repository,
            access_guard=self._access_guard,
        )


class ListWorkoutReportsForWeekUseCase:
    """Return completion reports for the last 7 days from anchor_date."""

    def __init__(
        self,
        report_repository: WorkoutCompletionReportRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._report_repository = report_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
        anchor_date: date | None = None,
    ) -> WorkoutReportSummaryView:
        return _list_workout_reports(
            actor_id=actor_id,
            actor_role=actor_role,
            athlete_id=athlete_id,
            anchor_date=anchor_date,
            period=REPORT_PERIOD_WEEK,
            date_range=report_week_range,
            report_repository=self._report_repository,
            access_guard=self._access_guard,
        )


class ListWorkoutReportsForMonthUseCase:
    """Return completion reports for the last 30 days from anchor_date."""

    def __init__(
        self,
        report_repository: WorkoutCompletionReportRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._report_repository = report_repository
        self._access_guard = access_guard

    def execute(
        self,
        actor_id: UserId,
        actor_role: Role,
        athlete_id: UserId,
        anchor_date: date | None = None,
    ) -> WorkoutReportSummaryView:
        return _list_workout_reports(
            actor_id=actor_id,
            actor_role=actor_role,
            athlete_id=athlete_id,
            anchor_date=anchor_date,
            period=REPORT_PERIOD_MONTH,
            date_range=report_month_range,
            report_repository=self._report_repository,
            access_guard=self._access_guard,
        )


def _get_training_calendar(
    *,
    actor_id: UserId,
    actor_role: Role,
    athlete_id: UserId,
    anchor_date: date | None,
    period: str,
    date_range: Callable[[date], tuple[date, date]],
    workout_repository: PlannedWorkoutRepository,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
    access_guard: TrainingAccessGuard,
) -> TrainingCalendarView:
    _ensure_training_view_access(actor_id, actor_role, athlete_id, access_guard)
    resolved_anchor = resolve_anchor_date(anchor_date)
    start_date, end_date = date_range(resolved_anchor)
    workouts = _list_workouts_for_actor(
        actor_id=actor_id,
        actor_role=actor_role,
        athlete_id=athlete_id,
        start_date=start_date,
        end_date=end_date,
        workout_repository=workout_repository,
    )
    workout_views = tuple(
        build_planned_workout_view(workout, cycle_repository, exercise_repository)
        for workout in workouts
    )
    return TrainingCalendarView(
        anchor_date=resolved_anchor,
        period=period,
        workouts=workout_views,
    )


def _list_workout_reports(
    *,
    actor_id: UserId,
    actor_role: Role,
    athlete_id: UserId,
    anchor_date: date | None,
    period: str,
    date_range: Callable[[date], tuple[datetime, datetime]],
    report_repository: WorkoutCompletionReportRepository,
    access_guard: TrainingAccessGuard,
) -> WorkoutReportSummaryView:
    _ensure_training_view_access(actor_id, actor_role, athlete_id, access_guard)
    resolved_anchor = resolve_anchor_date(anchor_date)
    start_at, end_at = date_range(resolved_anchor)
    reports = report_repository.list_by_athlete_and_date_range(
        athlete_id,
        start_at=start_at,
        end_at=end_at,
    )
    return WorkoutReportSummaryView(
        anchor_date=resolved_anchor,
        period=period,
        reports=tuple(WorkoutCompletionReportView.from_report(report) for report in reports),
    )


def _ensure_training_view_access(
    actor_id: UserId,
    actor_role: Role,
    athlete_id: UserId,
    access_guard: TrainingAccessGuard,
) -> None:
    if actor_role is Role.ATHLETE:
        access_guard.ensure_athlete_can_view_own_training(actor_id, athlete_id)
        return
    if actor_role is Role.COACH:
        access_guard.ensure_coach_can_view_athlete_training(actor_id, athlete_id)
        return
    raise AuthorizationError("Only coaches and athletes can view training data")


def _list_workouts_for_actor(
    *,
    actor_id: UserId,
    actor_role: Role,
    athlete_id: UserId,
    start_date: date,
    end_date: date,
    workout_repository: PlannedWorkoutRepository,
) -> list[PlannedWorkout]:
    if actor_role is Role.COACH:
        return workout_repository.list_by_coach_and_athlete_date_range(
            actor_id,
            athlete_id,
            start_date=start_date,
            end_date=end_date,
        )
    return workout_repository.list_by_athlete_and_date_range(
        athlete_id,
        start_date=start_date,
        end_date=end_date,
    )


def build_planned_workout_view(
    workout: PlannedWorkout,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
) -> PlannedWorkoutView:
    cycles = cycle_repository.list_by_workout(workout.id)
    cycle_views = tuple(
        WorkoutCycleView.from_cycle(
            cycle,
            tuple(
                WorkoutExerciseView.from_exercise(exercise)
                for exercise in exercise_repository.list_by_cycle(cycle.id)
            ),
        )
        for cycle in cycles
    )
    return PlannedWorkoutView.from_workout(workout, cycle_views)
