"""Use cases for MVP 2.1 indexing flows around raw training text."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from uuid import UUID

from application.dto.training_inputs import PlannedWorkoutInput
from application.security.training_access_guard import TrainingAccessGuard
from domain.entities.plan_scope import PlanScope
from domain.entities.role import Role
from domain.entities.training_plan import TrainingPlan
from domain.exceptions import (
    AuthorizationError,
    DomainError,
    DuplicatePlannedWorkoutError,
    TrainingPlanNotFoundError,
)
from domain.repositories.planned_workout_repository import PlannedWorkoutRepository
from domain.repositories.training_plan_repository import TrainingPlanRepository
from domain.repositories.workout_cycle_repository import WorkoutCycleRepository
from domain.repositories.workout_exercise_repository import WorkoutExerciseRepository
from domain.services.training_access import assert_workout_not_in_past
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_training_event
from infrastructure.parsing.rule_based_training_text_parser import count_day_headers


def _today_utc() -> date:
    return datetime.now(UTC).date()


def _resolve_parse_scope(
    *,
    requested_scope: PlanScope | None,
    plan_scope: PlanScope,
    raw_text: str,
) -> PlanScope:
    if requested_scope is not None:
        return requested_scope
    if count_day_headers(raw_text) >= 2:
        return PlanScope.WEEK
    return plan_scope


@dataclass(frozen=True, slots=True)
class UpdateTrainingPlanRawTextResult:
    plan: TrainingPlan
    replaced_workouts_count: int


class UpdateTrainingPlanRawTextUseCase:
    """Update plan raw text and re-parse future workouts only."""

    def __init__(
        self,
        plan_repository: TrainingPlanRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
        *,
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
        *,
        coach_id: UserId,
        coach_role: Role,
        plan_id: str,
        raw_text: str,
        titles: dict[str, str] | None = None,
        scope: PlanScope | None = None,
        start_date: date | None = None,
    ) -> UpdateTrainingPlanRawTextResult:
        """Replace workouts scheduled after today with parsed content from raw_text.

        Past workouts and their reports are preserved to avoid data loss.
        """
        try:
            if coach_role is not Role.COACH:
                raise AuthorizationError("Only coaches can update training plans")

            parsed_plan_id = TrainingPlanId(UUID(plan_id))
            plan = self._plan_repository.get_by_id(parsed_plan_id)
            if plan is None:
                raise TrainingPlanNotFoundError(f"Training plan not found: {plan_id}")
            if plan.coach_id != coach_id:
                raise AuthorizationError("Coach can only update their own training plans")

            self._access_guard.ensure_coach_can_access_athlete_training(coach_id, plan.athlete_id)

            effective_scope = _resolve_parse_scope(
                requested_scope=scope,
                plan_scope=plan.scope,
                raw_text=raw_text,
            )
            effective_start_date = start_date or plan.start_date

            today = _today_utc()
            existing_workouts = self._workout_repository.list_by_plan(plan.id)
            future_workouts = [w for w in existing_workouts if w.planned_date > today]

            for workout in future_workouts:
                self._workout_repository.delete(workout.id)

            from application.use_cases.training_commands import _persist_workout  # local import
            from application.use_cases.training_text_commands import (  # local import
                ParseTrainingPlanTextUseCase,
                _draft_workout_to_input,
                _validate_week_text_parsing,
            )

            parse_result = ParseTrainingPlanTextUseCase(access_guard=self._access_guard).execute(
                coach_id=coach_id,
                athlete_id=plan.athlete_id,
                scope=effective_scope,
                start_date=effective_start_date,
                text=raw_text,
            )
            if effective_scope is PlanScope.WEEK:
                _validate_week_text_parsing(text=raw_text, draft=parse_result.draft)

            inputs: list[PlannedWorkoutInput] = [
                _draft_workout_to_input(workout)
                for workout in parse_result.draft.workouts
                if workout.planned_date >= today
            ]

            replaced_count = 0
            for workout_input in inputs:
                assert_workout_not_in_past(workout_input.planned_date, today)
                existing_workout = self._workout_repository.get_by_athlete_and_date(
                    plan.athlete_id,
                    workout_input.planned_date,
                )
                if existing_workout is not None:
                    if existing_workout.coach_id != coach_id:
                        raise DuplicatePlannedWorkoutError(
                            f"Workout already exists for date {workout_input.planned_date}"
                        )
                    from application.use_cases.training_commands import (  # local import
                        _upsert_workout_for_plan,
                    )

                    _upsert_workout_for_plan(
                        plan=plan,
                        existing_workout=existing_workout,
                        workout_input=workout_input,
                        workout_repository=self._workout_repository,
                        cycle_repository=self._cycle_repository,
                        exercise_repository=self._exercise_repository,
                    )
                else:
                    _persist_workout(
                        plan=plan,
                        workout_input=workout_input,
                        workout_repository=self._workout_repository,
                        cycle_repository=self._cycle_repository,
                        exercise_repository=self._exercise_repository,
                    )
                replaced_count += 1

            if titles:
                for workout in self._workout_repository.list_by_plan(plan.id):
                    override = titles.get(workout.planned_date.isoformat())
                    if override is None:
                        continue
                    self._workout_repository.save(
                        replace(workout, title=override.strip() or None)
                    )

            updated_plan = TrainingPlan(
                id=plan.id,
                coach_id=plan.coach_id,
                athlete_id=plan.athlete_id,
                scope=effective_scope,
                start_date=effective_start_date,
                created_at=plan.created_at,
                raw_text=raw_text.strip() or None,
            )
            saved_plan = self._plan_repository.save(updated_plan)
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
            "training_plan_raw_text_updated",
            success=True,
            user_id=str(coach_id),
            message=f"Training plan raw text updated: {plan_id}",
        )
        return UpdateTrainingPlanRawTextResult(
            plan=saved_plan,
            replaced_workouts_count=replaced_count,
        )
