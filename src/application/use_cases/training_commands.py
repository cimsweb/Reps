"""Use cases for MVP 2 training write operations."""

import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from application.dto.training_inputs import PlannedWorkoutInput
from application.security.training_access_guard import TrainingAccessGuard
from domain.entities.plan_scope import PlanScope
from domain.entities.planned_workout import PlannedWorkout
from domain.entities.role import Role
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.entities.workout_cycle import WorkoutCycle
from domain.entities.workout_exercise import WorkoutExercise
from domain.entities.workout_type import WorkoutType
from domain.exceptions import (
    AuthorizationError,
    DomainError,
    DuplicatePlannedWorkoutError,
    InvalidTrainingPlanError,
    InvalidWorkoutStructureError,
    PlannedWorkoutNotFoundError,
    WorkoutReportAlreadyExistsError,
)
from domain.repositories.planned_workout_repository import PlannedWorkoutRepository
from domain.repositories.training_plan_repository import TrainingPlanRepository
from domain.repositories.workout_completion_report_repository import (
    WorkoutCompletionReportRepository,
)
from domain.repositories.workout_cycle_repository import WorkoutCycleRepository
from domain.repositories.workout_exercise_repository import WorkoutExerciseRepository
from domain.services.training_access import assert_workout_not_in_past
from domain.services.training_ownership import (
    assert_planned_workout_matches_plan,
    assert_report_matches_workout,
)
from domain.value_objects.difficulty_rating import DifficultyRating
from domain.value_objects.garmin_report_url import GarminReportUrl
from domain.value_objects.mood_rating import MoodRating
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_completion_report_id import WorkoutCompletionReportId
from domain.value_objects.workout_cycle_id import WorkoutCycleId
from domain.value_objects.workout_exercise_id import WorkoutExerciseId
from infrastructure.logging.setup import log_training_event


class CreateDayTrainingPlanUseCase:
    """Coach creates a training plan for a single day."""

    def __init__(
        self,
        plan_repository: TrainingPlanRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._plan_repository = plan_repository
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.training")

    def execute(
        self,
        coach_id: UserId,
        coach_role: Role,
        athlete_id: UserId,
        start_date: date,
        workouts: list[PlannedWorkoutInput],
    ) -> TrainingPlan:
        """Create a day plan with one or more workouts on start_date."""
        return _create_training_plan(
            coach_id=coach_id,
            coach_role=coach_role,
            athlete_id=athlete_id,
            scope=PlanScope.DAY,
            start_date=start_date,
            workouts=workouts,
            plan_repository=self._plan_repository,
            workout_repository=self._workout_repository,
            cycle_repository=self._cycle_repository,
            exercise_repository=self._exercise_repository,
            access_guard=self._access_guard,
            logger=self._logger,
            validate_dates=_validate_day_plan_dates,
        )


class CreateWeekTrainingPlanUseCase:
    """Coach creates a training plan for one week."""

    def __init__(
        self,
        plan_repository: TrainingPlanRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._plan_repository = plan_repository
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.training")

    def execute(
        self,
        coach_id: UserId,
        coach_role: Role,
        athlete_id: UserId,
        start_date: date,
        workouts: list[PlannedWorkoutInput],
    ) -> TrainingPlan:
        """Create a week plan with workouts from start_date through start_date + 6 days."""
        return _create_training_plan(
            coach_id=coach_id,
            coach_role=coach_role,
            athlete_id=athlete_id,
            scope=PlanScope.WEEK,
            start_date=start_date,
            workouts=workouts,
            plan_repository=self._plan_repository,
            workout_repository=self._workout_repository,
            cycle_repository=self._cycle_repository,
            exercise_repository=self._exercise_repository,
            access_guard=self._access_guard,
            logger=self._logger,
            validate_dates=_validate_week_plan_dates,
        )


class UpdatePlannedWorkoutUseCase:
    """Coach updates a planned workout."""

    def __init__(
        self,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.training")

    def execute(
        self,
        coach_id: UserId,
        coach_role: Role,
        workout_id: str,
        workout_input: PlannedWorkoutInput,
    ) -> PlannedWorkout:
        """Update workout fields, cycles, and exercises."""
        try:
            if coach_role is not Role.COACH:
                raise AuthorizationError("Only coaches can update planned workouts")

            parsed_workout_id = PlannedWorkoutId(UUID(workout_id))
            existing_workout = self._workout_repository.get_by_id(parsed_workout_id)
            if existing_workout is None:
                raise PlannedWorkoutNotFoundError(f"Planned workout not found: {workout_id}")
            if existing_workout.coach_id != coach_id:
                raise AuthorizationError("Coach can only update their own planned workouts")

            self._access_guard.ensure_coach_can_access_athlete_training(
                coach_id,
                existing_workout.athlete_id,
            )
            assert_workout_not_in_past(existing_workout.planned_date, _today_utc())

            if (
                workout_input.planned_date != existing_workout.planned_date
                and self._workout_repository.get_by_athlete_and_date(
                    existing_workout.athlete_id,
                    workout_input.planned_date,
                )
                is not None
            ):
                raise DuplicatePlannedWorkoutError(
                    f"Workout already exists for date {workout_input.planned_date}"
                )

            parsed_workout_type = _parse_workout_type(workout_input.workout_type)
            _validate_workout_structure(workout_input)

            updated_workout = PlannedWorkout(
                id=existing_workout.id,
                plan_id=existing_workout.plan_id,
                coach_id=existing_workout.coach_id,
                athlete_id=existing_workout.athlete_id,
                planned_date=workout_input.planned_date,
                workout_type=parsed_workout_type,
                title=workout_input.title,
                created_at=existing_workout.created_at,
            )
            saved_workout = self._workout_repository.save(updated_workout)
            _replace_workout_structure(
                saved_workout.id,
                workout_input,
                self._cycle_repository,
                self._exercise_repository,
            )
        except DomainError as error:
            log_training_event(
                self._logger,
                "training_validation_error",
                success=False,
                user_id=str(coach_id),
                message=str(error),
            )
            raise

        log_training_event(
            self._logger,
            "training_plan_updated",
            success=True,
            user_id=str(coach_id),
            message=f"Planned workout updated: {workout_id}",
        )
        return saved_workout


class DeletePlannedWorkoutUseCase:
    """Coach deletes a planned workout."""

    def __init__(
        self,
        workout_repository: PlannedWorkoutRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._workout_repository = workout_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.training")

    def execute(self, coach_id: UserId, coach_role: Role, workout_id: str) -> None:
        """Delete a future planned workout."""
        try:
            if coach_role is not Role.COACH:
                raise AuthorizationError("Only coaches can delete planned workouts")

            parsed_workout_id = PlannedWorkoutId(UUID(workout_id))
            existing_workout = self._workout_repository.get_by_id(parsed_workout_id)
            if existing_workout is None:
                raise PlannedWorkoutNotFoundError(f"Planned workout not found: {workout_id}")
            if existing_workout.coach_id != coach_id:
                raise AuthorizationError("Coach can only delete their own planned workouts")

            self._access_guard.ensure_coach_can_access_athlete_training(
                coach_id,
                existing_workout.athlete_id,
            )
            assert_workout_not_in_past(existing_workout.planned_date, _today_utc())
            self._workout_repository.delete(parsed_workout_id)
        except DomainError as error:
            log_training_event(
                self._logger,
                "training_validation_error",
                success=False,
                user_id=str(coach_id),
                message=str(error),
            )
            raise

        log_training_event(
            self._logger,
            "training_plan_updated",
            success=True,
            user_id=str(coach_id),
            message=f"Planned workout deleted: {workout_id}",
        )


class SubmitWorkoutCompletionReportUseCase:
    """Athlete submits a completion report for a planned workout."""

    def __init__(
        self,
        workout_repository: PlannedWorkoutRepository,
        report_repository: WorkoutCompletionReportRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._workout_repository = workout_repository
        self._report_repository = report_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.training")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        workout_id: str,
        difficulty_rating: int,
        mood_rating: int,
        comment: str | None = None,
        garmin_url: str | None = None,
        raw_report_text: str | None = None,
    ) -> WorkoutCompletionReport:
        """Save athlete report with difficulty and mood ratings."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can submit workout reports")

            parsed_workout_id = PlannedWorkoutId(UUID(workout_id))
            workout = self._workout_repository.get_by_id(parsed_workout_id)
            if workout is None:
                raise PlannedWorkoutNotFoundError(f"Planned workout not found: {workout_id}")

            self._access_guard.ensure_athlete_owns_workout(athlete_id, workout.athlete_id)

            if self._report_repository.get_by_planned_workout(parsed_workout_id) is not None:
                raise WorkoutReportAlreadyExistsError(
                    f"Report already exists for workout: {workout_id}"
                )

            normalized_comment = comment.strip() if comment else None
            normalized_garmin_url = garmin_url.strip() if garmin_url else None
            normalized_raw_report_text = raw_report_text.strip() if raw_report_text else None
            validated_garmin_url = (
                str(GarminReportUrl(normalized_garmin_url)) if normalized_garmin_url else None
            )
            report = WorkoutCompletionReport(
                id=WorkoutCompletionReportId(uuid4()),
                planned_workout_id=parsed_workout_id,
                athlete_id=athlete_id,
                difficulty_rating=DifficultyRating(difficulty_rating),
                mood_rating=MoodRating(mood_rating),
                comment=normalized_comment,
                garmin_url=validated_garmin_url,
                raw_report_text=normalized_raw_report_text,
                created_at=datetime.now(UTC),
            )
            assert_report_matches_workout(report, workout)
            saved_report = self._report_repository.save(report)
        except DomainError as error:
            log_training_event(
                self._logger,
                "training_validation_error",
                success=False,
                user_id=str(athlete_id),
                message=str(error),
            )
            raise

        log_training_event(
            self._logger,
            "workout_completion_report_submitted",
            success=True,
            user_id=str(athlete_id),
            message=f"Workout report submitted for {workout_id}",
        )
        return saved_report


def _create_training_plan(
    *,
    coach_id: UserId,
    coach_role: Role,
    athlete_id: UserId,
    scope: PlanScope,
    start_date: date,
    workouts: list[PlannedWorkoutInput],
    plan_repository: TrainingPlanRepository,
    workout_repository: PlannedWorkoutRepository,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
    access_guard: TrainingAccessGuard,
    logger: logging.Logger,
    validate_dates: Callable[[date, list[PlannedWorkoutInput]], None],
) -> TrainingPlan:
    try:
        if coach_role is not Role.COACH:
            raise AuthorizationError("Only coaches can create training plans")
        if not workouts:
            raise InvalidTrainingPlanError("Training plan must include at least one workout")

        access_guard.ensure_coach_can_access_athlete_training(coach_id, athlete_id)
        validate_dates(start_date, workouts)

        plan = TrainingPlan(
            id=TrainingPlanId(uuid4()),
            coach_id=coach_id,
            athlete_id=athlete_id,
            scope=scope,
            start_date=start_date,
            created_at=datetime.now(UTC),
        )
        saved_plan = plan_repository.save(plan)

        for workout_input in workouts:
            existing_workout = workout_repository.get_by_athlete_and_date(
                athlete_id,
                workout_input.planned_date,
            )
            if existing_workout is not None:
                if existing_workout.coach_id != coach_id:
                    raise DuplicatePlannedWorkoutError(
                        f"Workout already exists for date {workout_input.planned_date}"
                    )
                _upsert_workout_for_plan(
                    plan=saved_plan,
                    existing_workout=existing_workout,
                    workout_input=workout_input,
                    workout_repository=workout_repository,
                    cycle_repository=cycle_repository,
                    exercise_repository=exercise_repository,
                )
            else:
                _persist_workout(
                    plan=saved_plan,
                    workout_input=workout_input,
                    workout_repository=workout_repository,
                    cycle_repository=cycle_repository,
                    exercise_repository=exercise_repository,
                )
    except DomainError as error:
        log_training_event(
            logger,
            "training_validation_error",
            success=False,
            user_id=str(coach_id),
            message=str(error),
        )
        raise

    log_training_event(
        logger,
        "training_plan_created",
        success=True,
        user_id=str(coach_id),
        message=f"Training plan created for athlete {athlete_id.value}",
    )
    return saved_plan


def _validate_day_plan_dates(start_date: date, workouts: list[PlannedWorkoutInput]) -> None:
    for workout_input in workouts:
        if workout_input.planned_date != start_date:
            raise InvalidTrainingPlanError("Day plan workouts must use the same date as start_date")


def _validate_week_plan_dates(start_date: date, workouts: list[PlannedWorkoutInput]) -> None:
    end_date = start_date + timedelta(days=6)
    for workout_input in workouts:
        if workout_input.planned_date < start_date or workout_input.planned_date > end_date:
            raise InvalidTrainingPlanError(
                f"Workout date {workout_input.planned_date} is outside the week plan range"
            )


def _parse_workout_type(workout_type: str) -> WorkoutType:
    try:
        return WorkoutType(workout_type)
    except ValueError as error:
        raise InvalidWorkoutStructureError(f"Unknown workout type: {workout_type}") from error


def _validate_workout_structure(workout_input: PlannedWorkoutInput) -> None:
    if not workout_input.cycles:
        raise InvalidWorkoutStructureError("Workout must include at least one cycle")
    for cycle_input in workout_input.cycles:
        if not cycle_input.exercises:
            raise InvalidWorkoutStructureError(
                f"Cycle '{cycle_input.name}' must include at least one exercise"
            )
        if not cycle_input.name.strip():
            raise InvalidWorkoutStructureError("Cycle name cannot be empty")
        for exercise_input in cycle_input.exercises:
            if not exercise_input.name.strip():
                raise InvalidWorkoutStructureError("Exercise name cannot be empty")


def _persist_workout(
    *,
    plan: TrainingPlan,
    workout_input: PlannedWorkoutInput,
    workout_repository: PlannedWorkoutRepository,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
) -> PlannedWorkout:
    parsed_workout_type = _parse_workout_type(workout_input.workout_type)
    _validate_workout_structure(workout_input)

    workout = PlannedWorkout(
        id=PlannedWorkoutId(uuid4()),
        plan_id=plan.id,
        coach_id=plan.coach_id,
        athlete_id=plan.athlete_id,
        planned_date=workout_input.planned_date,
        workout_type=parsed_workout_type,
        title=workout_input.title,
        created_at=datetime.now(UTC),
    )
    assert_planned_workout_matches_plan(workout, plan)
    saved_workout = workout_repository.save(workout)
    _save_workout_structure(
        saved_workout.id,
        workout_input,
        cycle_repository,
        exercise_repository,
    )
    return saved_workout


def _upsert_workout_for_plan(
    *,
    plan: TrainingPlan,
    existing_workout: PlannedWorkout,
    workout_input: PlannedWorkoutInput,
    workout_repository: PlannedWorkoutRepository,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
) -> PlannedWorkout:
    parsed_workout_type = _parse_workout_type(workout_input.workout_type)
    _validate_workout_structure(workout_input)

    updated_workout = PlannedWorkout(
        id=existing_workout.id,
        plan_id=plan.id,
        coach_id=plan.coach_id,
        athlete_id=plan.athlete_id,
        planned_date=workout_input.planned_date,
        workout_type=parsed_workout_type,
        title=workout_input.title,
        created_at=existing_workout.created_at,
    )
    assert_planned_workout_matches_plan(updated_workout, plan)
    saved_workout = workout_repository.save(updated_workout)
    _replace_workout_structure(
        saved_workout.id,
        workout_input,
        cycle_repository,
        exercise_repository,
    )
    return saved_workout


def _save_workout_structure(
    workout_id: PlannedWorkoutId,
    workout_input: PlannedWorkoutInput,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
) -> None:
    for cycle_input in workout_input.cycles:
        cycle = WorkoutCycle(
            id=WorkoutCycleId(uuid4()),
            planned_workout_id=workout_id,
            name=cycle_input.name.strip(),
            sort_order=cycle_input.sort_order,
        )
        cycle_repository.save(cycle)
        for exercise_input in cycle_input.exercises:
            exercise_repository.save(
                WorkoutExercise(
                    id=WorkoutExerciseId(uuid4()),
                    cycle_id=cycle.id,
                    name=exercise_input.name.strip(),
                    details=exercise_input.details.strip(),
                    sort_order=exercise_input.sort_order,
                )
            )


def _replace_workout_structure(
    workout_id: PlannedWorkoutId,
    workout_input: PlannedWorkoutInput,
    cycle_repository: WorkoutCycleRepository,
    exercise_repository: WorkoutExerciseRepository,
) -> None:
    existing_cycles = cycle_repository.list_by_workout(workout_id)
    for cycle in existing_cycles:
        exercise_repository.delete_by_cycle(cycle.id)
    cycle_repository.delete_by_workout(workout_id)
    _save_workout_structure(workout_id, workout_input, cycle_repository, exercise_repository)


def _today_utc() -> date:
    return datetime.now(UTC).date()
