"""Use cases for MVP 2.1 training text parsing."""

from dataclasses import dataclass, replace
from datetime import date

from application.dto.training_inputs import (
    PlannedWorkoutInput,
    WorkoutCycleInput,
    WorkoutExerciseInput,
)
from application.security.training_access_guard import TrainingAccessGuard
from domain.entities.plan_scope import PlanScope
from domain.entities.role import Role
from domain.entities.training_plan import TrainingPlan
from domain.exceptions import InvalidTrainingPlanError
from domain.repositories.planned_workout_repository import PlannedWorkoutRepository
from domain.repositories.training_plan_repository import TrainingPlanRepository
from domain.repositories.workout_cycle_repository import WorkoutCycleRepository
from domain.repositories.workout_exercise_repository import WorkoutExerciseRepository
from domain.services.training_text_parsing import (
    ParsedTrainingDraft,
    ParsedWorkoutDraft,
    ReportDraft,
)
from domain.value_objects.user_id import UserId
from infrastructure.parsing.rule_based_report_text_parser import RuleBasedReportTextParser
from infrastructure.parsing.rule_based_training_text_parser import (
    RuleBasedTrainingTextParser,
    count_day_headers,
)


@dataclass(frozen=True, slots=True)
class ParseTrainingPlanTextResult:
    draft: ParsedTrainingDraft
    detected_scope: PlanScope


class ParseTrainingPlanTextUseCase:
    def __init__(self, *, access_guard: TrainingAccessGuard) -> None:
        self._access_guard = access_guard
        self._parser = RuleBasedTrainingTextParser()

    def execute(
        self,
        *,
        coach_id: UserId,
        athlete_id: UserId,
        scope: PlanScope,
        start_date: date,
        text: str,
    ) -> ParseTrainingPlanTextResult:
        self._access_guard.ensure_coach_can_access_athlete_training(coach_id, athlete_id)
        draft = (
            self._parser.parse_day(text=text, planned_date=start_date)
            if scope is PlanScope.DAY
            else self._parser.parse_week(text=text, start_date=start_date)
        )
        return ParseTrainingPlanTextResult(draft=draft, detected_scope=scope)


class CreateTrainingPlanFromTextUseCase:
    def __init__(
        self,
        *,
        plan_repository: TrainingPlanRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._plan_repository = plan_repository
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard
        self._parser = RuleBasedTrainingTextParser()

    def execute(
        self,
        *,
        coach_id: UserId,
        coach_role: Role,
        athlete_id: UserId,
        scope: PlanScope,
        start_date: date,
        text: str,
        title: str | None = None,
        titles: dict[str, str] | None = None,
    ) -> TrainingPlan:
        from application.use_cases.training_commands import (  # local import to avoid cycles
            CreateDayTrainingPlanUseCase,
            CreateWeekTrainingPlanUseCase,
        )

        self._access_guard.ensure_coach_can_access_athlete_training(coach_id, athlete_id)
        draft = (
            self._parser.parse_day(text=text, planned_date=start_date)
            if scope is PlanScope.DAY
            else self._parser.parse_week(text=text, start_date=start_date)
        )
        draft = _apply_title_overrides(
            draft,
            scope=scope,
            title=title,
            titles=titles,
        )
        if scope is PlanScope.WEEK:
            _validate_week_text_parsing(text=text, draft=draft)
        workouts_inputs = [_draft_workout_to_input(workout) for workout in draft.workouts]
        create_day = CreateDayTrainingPlanUseCase(
            self._plan_repository,
            self._workout_repository,
            self._cycle_repository,
            self._exercise_repository,
            self._access_guard,
        )
        create_week = CreateWeekTrainingPlanUseCase(
            self._plan_repository,
            self._workout_repository,
            self._cycle_repository,
            self._exercise_repository,
            self._access_guard,
        )

        plan = (
            create_day.execute(coach_id, coach_role, athlete_id, start_date, workouts_inputs)
            if scope is PlanScope.DAY
            else create_week.execute(coach_id, coach_role, athlete_id, start_date, workouts_inputs)
        )

        # Persist original text for editing UX (MVP 2.1-003 updates may add re-parse).
        plan_with_raw = TrainingPlan(
            id=plan.id,
            coach_id=plan.coach_id,
            athlete_id=plan.athlete_id,
            scope=plan.scope,
            start_date=plan.start_date,
            created_at=plan.created_at,
            raw_text=text.strip() or None,
        )
        return self._plan_repository.save(plan_with_raw)


class ParseWorkoutReportTextUseCase:
    def __init__(self) -> None:
        self._parser = RuleBasedReportTextParser()

    def execute(
        self,
        *,
        athlete_id: UserId,
        text: str,
    ) -> ReportDraft:
        return self._parser.parse_report_text(text=text)


def _validate_week_text_parsing(*, text: str, draft: ParsedTrainingDraft) -> None:
    """Reject week plans where multi-day text collapsed into a single workout."""
    header_count = count_day_headers(text)
    workout_count = len(draft.workouts)
    if header_count >= 2 and workout_count < 2:
        raise InvalidTrainingPlanError(
            "Не удалось разбить текст недели по дням. "
            "Используйте заголовки вида '7 Июля' для каждого дня."
        )


def _apply_title_overrides(
    draft: ParsedTrainingDraft,
    *,
    scope: PlanScope,
    title: str | None,
    titles: dict[str, str] | None,
) -> ParsedTrainingDraft:
    updated_workouts: list[ParsedWorkoutDraft] = []
    for workout in draft.workouts:
        next_title = workout.title
        if scope is PlanScope.DAY and title is not None:
            next_title = title.strip() or None
        elif titles is not None:
            override = titles.get(workout.planned_date.isoformat())
            if override is not None:
                next_title = override.strip() or None
        if next_title != workout.title:
            workout = replace(workout, title=next_title)
        updated_workouts.append(workout)
    return replace(draft, workouts=tuple(updated_workouts))


def _draft_workout_to_input(workout: ParsedWorkoutDraft) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=workout.planned_date,
        workout_type=workout.workout_type.value,
        title=workout.title,
        cycles=tuple(
            WorkoutCycleInput(
                name=cycle.name,
                sort_order=cycle.sort_order,
                exercises=tuple(
                    WorkoutExerciseInput(
                        name=exercise.name,
                        details=exercise.details,
                        sort_order=exercise.sort_order,
                    )
                    for exercise in cycle.exercises
                ),
            )
            for cycle in workout.cycles
        ),
    )
