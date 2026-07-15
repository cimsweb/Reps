from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from application.dto.training import (
    PlannedWorkoutView,
    TrainingCalendarView,
    TrainingPlanView,
    WorkoutCompletionReportView,
    WorkoutCycleView,
    WorkoutExerciseView,
    WorkoutReportSummaryView,
)
from application.dto.training_inputs import (
    PlannedWorkoutInput,
    WorkoutCycleInput,
    WorkoutExerciseInput,
)
from application.services.training_plan_text_export import format_training_calendar_as_text
from application.use_cases.training_commands import (
    CreateDayTrainingPlanUseCase,
    CreateWeekTrainingPlanUseCase,
    DeletePlannedWorkoutUseCase,
    SubmitWorkoutCompletionReportUseCase,
    UpdatePlannedWorkoutUseCase,
)
from application.use_cases.training_queries import (
    GetTrainingPlanForMonthUseCase,
    GetTrainingPlanForWeekUseCase,
    ListWorkoutReportsForMonthUseCase,
    ListWorkoutReportsForWeekUseCase,
    build_planned_workout_view,
)
from application.use_cases.training_text_commands import (
    CreateTrainingPlanFromTextUseCase,
    ParseTrainingPlanTextUseCase,
)
from application.use_cases.training_text_indexing import UpdateTrainingPlanRawTextUseCase
from domain.entities.plan_scope import PlanScope
from domain.entities.planned_workout import PlannedWorkout
from domain.entities.role import Role
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.services.authorization import Permission
from domain.services.training_periods import PLAN_PERIOD_MONTH, REPORT_PERIOD_MONTH
from domain.value_objects.user_id import UserId
from infrastructure.db.training_repositories import (
    SqlAlchemyPlannedWorkoutRepository,
    SqlAlchemyTrainingPlanRepository,
    SqlAlchemyWorkoutCompletionReportRepository,
    SqlAlchemyWorkoutCycleRepository,
    SqlAlchemyWorkoutExerciseRepository,
)
from interfaces.http.dependencies import (
    AuthorizationGuardDep,
    DbSession,
    TrainingAccessGuardDep,
    get_bearer_token,
)
from interfaces.http.schemas import (
    CreateTrainingPlanRequest,
    ParsedPlannedWorkoutDraftResponse,
    ParsedWorkoutCycleDraftResponse,
    ParsedWorkoutExerciseDraftResponse,
    ParseTrainingPlanTextRequest,
    ParseTrainingPlanTextResponse,
    PlannedWorkoutRequest,
    PlannedWorkoutResponse,
    SubmitWorkoutReportRequest,
    TrainingCalendarResponse,
    TrainingPlanResponse,
    TrainingPlanTextResponse,
    UpdateTrainingPlanRawTextRequest,
    UpdateTrainingPlanRawTextResponse,
    WorkoutCompletionReportResponse,
    WorkoutCycleResponse,
    WorkoutExerciseResponse,
    WorkoutReportSummaryResponse,
)

router = APIRouter(tags=["training"])


def _parse_user_id(user_id: str) -> UserId:
    return UserId(UUID(user_id))


def _workout_request_to_input(request: PlannedWorkoutRequest) -> PlannedWorkoutInput:
    return PlannedWorkoutInput(
        planned_date=request.planned_date,
        workout_type=request.workout_type,
        title=request.title,
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
            for cycle in request.cycles
        ),
    )


def _exercise_to_response(view: WorkoutExerciseView) -> WorkoutExerciseResponse:
    return WorkoutExerciseResponse(
        id=view.id,
        name=view.name,
        details=view.details,
        sort_order=view.sort_order,
    )


def _cycle_to_response(view: WorkoutCycleView) -> WorkoutCycleResponse:
    return WorkoutCycleResponse(
        id=view.id,
        name=view.name,
        sort_order=view.sort_order,
        exercises=[_exercise_to_response(exercise) for exercise in view.exercises],
    )


def _workout_view_to_response(view: PlannedWorkoutView) -> PlannedWorkoutResponse:
    return PlannedWorkoutResponse(
        id=view.id,
        plan_id=view.plan_id,
        coach_id=view.coach_id,
        athlete_id=view.athlete_id,
        planned_date=view.planned_date,
        workout_type=view.workout_type,
        title=view.title,
        created_at=view.created_at,
        cycles=[_cycle_to_response(cycle) for cycle in view.cycles],
    )


def _workout_entity_to_response(
    workout: PlannedWorkout,
    db: DbSession,
) -> PlannedWorkoutResponse:
    cycle_repository = SqlAlchemyWorkoutCycleRepository(db)
    exercise_repository = SqlAlchemyWorkoutExerciseRepository(db)
    return _workout_view_to_response(
        build_planned_workout_view(workout, cycle_repository, exercise_repository)
    )


def _plan_view_to_response(view: TrainingPlanView) -> TrainingPlanResponse:
    return TrainingPlanResponse(
        id=view.id,
        coach_id=view.coach_id,
        athlete_id=view.athlete_id,
        scope=view.scope,
        start_date=view.start_date,
        created_at=view.created_at,
        raw_text=view.raw_text,
        workouts=[_workout_view_to_response(workout) for workout in view.workouts],
    )


def _plan_entity_to_response(plan: TrainingPlan, db: DbSession) -> TrainingPlanResponse:
    workout_repository = SqlAlchemyPlannedWorkoutRepository(db)
    cycle_repository = SqlAlchemyWorkoutCycleRepository(db)
    exercise_repository = SqlAlchemyWorkoutExerciseRepository(db)
    workouts = workout_repository.list_by_plan(plan.id)
    workout_views = tuple(
        build_planned_workout_view(workout, cycle_repository, exercise_repository)
        for workout in workouts
    )
    return _plan_view_to_response(TrainingPlanView.from_plan(plan, workout_views))


def _calendar_to_response(view: TrainingCalendarView) -> TrainingCalendarResponse:
    return TrainingCalendarResponse(
        anchor_date=view.anchor_date,
        period=view.period,
        workouts=[_workout_view_to_response(workout) for workout in view.workouts],
    )


def _report_view_to_response(view: WorkoutCompletionReportView) -> WorkoutCompletionReportResponse:
    return WorkoutCompletionReportResponse(
        id=view.id,
        planned_workout_id=view.planned_workout_id,
        athlete_id=view.athlete_id,
        difficulty_rating=view.difficulty_rating,
        mood_rating=view.mood_rating,
        comment=view.comment,
        garmin_url=view.garmin_url,
        raw_report_text=view.raw_report_text,
        created_at=view.created_at,
    )


def _report_entity_to_response(report: WorkoutCompletionReport) -> WorkoutCompletionReportResponse:
    return _report_view_to_response(WorkoutCompletionReportView.from_report(report))


def _reports_to_response(view: WorkoutReportSummaryView) -> WorkoutReportSummaryResponse:
    return WorkoutReportSummaryResponse(
        anchor_date=view.anchor_date,
        period=view.period,
        reports=[_report_view_to_response(report) for report in view.reports],
    )


def _training_repositories(
    db: DbSession,
) -> tuple[
    SqlAlchemyTrainingPlanRepository,
    SqlAlchemyPlannedWorkoutRepository,
    SqlAlchemyWorkoutCycleRepository,
    SqlAlchemyWorkoutExerciseRepository,
]:
    return (
        SqlAlchemyTrainingPlanRepository(db),
        SqlAlchemyPlannedWorkoutRepository(db),
        SqlAlchemyWorkoutCycleRepository(db),
        SqlAlchemyWorkoutExerciseRepository(db),
    )


def _get_training_plan(
    *,
    db: DbSession,
    access_guard: TrainingAccessGuardDep,
    actor_id: UserId,
    actor_role: Role,
    athlete_id: UserId,
    period: str,
    anchor_date: date | None,
) -> TrainingCalendarView:
    plan_repository, workout_repository, cycle_repository, exercise_repository = (
        _training_repositories(db)
    )
    if period == PLAN_PERIOD_MONTH:
        return GetTrainingPlanForMonthUseCase(
            workout_repository,
            cycle_repository,
            exercise_repository,
            access_guard,
        ).execute(actor_id, actor_role, athlete_id, anchor_date)
    return GetTrainingPlanForWeekUseCase(
        workout_repository,
        cycle_repository,
        exercise_repository,
        access_guard,
    ).execute(actor_id, actor_role, athlete_id, anchor_date)


def _list_workout_reports(
    *,
    db: DbSession,
    access_guard: TrainingAccessGuardDep,
    actor_id: UserId,
    actor_role: Role,
    athlete_id: UserId,
    period: str,
    anchor_date: date | None,
) -> WorkoutReportSummaryView:
    report_repository = SqlAlchemyWorkoutCompletionReportRepository(db)
    if period == REPORT_PERIOD_MONTH:
        return ListWorkoutReportsForMonthUseCase(report_repository, access_guard).execute(
            actor_id,
            actor_role,
            athlete_id,
            anchor_date,
        )
    return ListWorkoutReportsForWeekUseCase(report_repository, access_guard).execute(
        actor_id,
        actor_role,
        athlete_id,
        anchor_date,
    )


@router.post(
    "/coach/athletes/{athlete_id}/training-plans/day",
    response_model=TrainingPlanResponse,
    status_code=201,
)
def create_day_training_plan(
    athlete_id: str,
    body: CreateTrainingPlanRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> TrainingPlanResponse:
    """Create a training plan for a single day."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    plan_repository, workout_repository, cycle_repository, exercise_repository = (
        _training_repositories(db)
    )
    plan = CreateDayTrainingPlanUseCase(
        plan_repository,
        workout_repository,
        cycle_repository,
        exercise_repository,
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        _parse_user_id(athlete_id),
        body.start_date,
        [_workout_request_to_input(workout) for workout in body.workouts],
    )
    return _plan_entity_to_response(plan, db)


@router.post(
    "/coach/athletes/{athlete_id}/training-plans/week",
    response_model=TrainingPlanResponse,
    status_code=201,
)
def create_week_training_plan(
    athlete_id: str,
    body: CreateTrainingPlanRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> TrainingPlanResponse:
    """Create a training plan for one week."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    plan_repository, workout_repository, cycle_repository, exercise_repository = (
        _training_repositories(db)
    )
    plan = CreateWeekTrainingPlanUseCase(
        plan_repository,
        workout_repository,
        cycle_repository,
        exercise_repository,
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        _parse_user_id(athlete_id),
        body.start_date,
        [_workout_request_to_input(workout) for workout in body.workouts],
    )
    return _plan_entity_to_response(plan, db)


@router.post(
    "/coach/athletes/{athlete_id}/training-plans/parse",
    response_model=ParseTrainingPlanTextResponse,
)
def parse_training_plan_text(
    athlete_id: str,
    body: ParseTrainingPlanTextRequest,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> ParseTrainingPlanTextResponse:
    """Parse training plan free text without saving (MVP 2.1)."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    use_case = ParseTrainingPlanTextUseCase(access_guard=access_guard)
    result = use_case.execute(
        coach_id=authenticated_user.user.id,
        athlete_id=_parse_user_id(athlete_id),
        scope=PlanScope(body.scope),
        start_date=body.start_date,
        text=body.text,
    )
    return ParseTrainingPlanTextResponse(
        detected_scope=result.detected_scope.value,
        warnings=list(result.draft.warnings),
        workouts=[
            ParsedPlannedWorkoutDraftResponse(
                planned_date=workout.planned_date,
                workout_type=workout.workout_type.value,
                title=workout.title,
                cycles=[
                    ParsedWorkoutCycleDraftResponse(
                        name=cycle.name,
                        sort_order=cycle.sort_order,
                        exercises=[
                            ParsedWorkoutExerciseDraftResponse(
                                name=exercise.name,
                                details=exercise.details,
                                sort_order=exercise.sort_order,
                            )
                            for exercise in cycle.exercises
                        ],
                    )
                    for cycle in workout.cycles
                ],
            )
            for workout in result.draft.workouts
        ],
    )


@router.post(
    "/coach/athletes/{athlete_id}/training-plans/from-text",
    response_model=TrainingPlanResponse,
    status_code=201,
)
def create_training_plan_from_text(
    athlete_id: str,
    body: ParseTrainingPlanTextRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> TrainingPlanResponse:
    """Create a training plan from free text (MVP 2.1)."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    plan_repository, workout_repository, cycle_repository, exercise_repository = (
        _training_repositories(db)
    )
    use_case = CreateTrainingPlanFromTextUseCase(
        plan_repository=plan_repository,
        workout_repository=workout_repository,
        cycle_repository=cycle_repository,
        exercise_repository=exercise_repository,
        access_guard=access_guard,
    )
    plan = use_case.execute(
        coach_id=authenticated_user.user.id,
        coach_role=authenticated_user.user.role,
        athlete_id=_parse_user_id(athlete_id),
        scope=PlanScope(body.scope),
        start_date=body.start_date,
        text=body.text,
        title=body.title,
        titles=body.titles,
    )
    return _plan_entity_to_response(plan, db)


@router.patch(
    "/coach/training-plans/{plan_id}/raw-text",
    response_model=UpdateTrainingPlanRawTextResponse,
)
def update_training_plan_raw_text(
    plan_id: str,
    body: UpdateTrainingPlanRawTextRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> UpdateTrainingPlanRawTextResponse:
    """Update training plan raw text and re-parse future workouts (MVP 2.1)."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    plan_repository = SqlAlchemyTrainingPlanRepository(db)
    workout_repository = SqlAlchemyPlannedWorkoutRepository(db)
    cycle_repository = SqlAlchemyWorkoutCycleRepository(db)
    exercise_repository = SqlAlchemyWorkoutExerciseRepository(db)

    result = UpdateTrainingPlanRawTextUseCase(
        plan_repository,
        workout_repository,
        cycle_repository,
        exercise_repository,
        access_guard,
    ).execute(
        coach_id=authenticated_user.user.id,
        coach_role=authenticated_user.user.role,
        plan_id=plan_id,
        raw_text=body.raw_text or "",
        titles=body.titles,
        scope=PlanScope(body.scope) if body.scope else None,
        start_date=body.start_date,
    )

    return UpdateTrainingPlanRawTextResponse(
        plan=_plan_entity_to_response(result.plan, db),
        replaced_workouts_count=result.replaced_workouts_count,
    )


@router.put("/coach/planned-workouts/{workout_id}", response_model=PlannedWorkoutResponse)
def update_planned_workout(
    workout_id: str,
    body: PlannedWorkoutRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> PlannedWorkoutResponse:
    """Update a planned workout."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    _, workout_repository, cycle_repository, exercise_repository = _training_repositories(db)
    workout = UpdatePlannedWorkoutUseCase(
        workout_repository,
        cycle_repository,
        exercise_repository,
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        workout_id,
        _workout_request_to_input(body),
    )
    return _workout_entity_to_response(workout, db)


@router.delete("/coach/planned-workouts/{workout_id}", status_code=204)
def delete_planned_workout(
    workout_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> Response:
    """Delete a planned workout."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    workout_repository = SqlAlchemyPlannedWorkoutRepository(db)
    DeletePlannedWorkoutUseCase(workout_repository, access_guard).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        workout_id,
    )
    return Response(status_code=204)


@router.post(
    "/athlete/planned-workouts/{workout_id}/report",
    response_model=WorkoutCompletionReportResponse,
    status_code=201,
)
def submit_workout_report(
    workout_id: str,
    body: SubmitWorkoutReportRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> WorkoutCompletionReportResponse:
    """Submit a workout completion report."""
    authenticated_user = guard.authorize(token, Permission.SUBMIT_WORKOUT_REPORT)
    workout_repository = SqlAlchemyPlannedWorkoutRepository(db)
    report_repository = SqlAlchemyWorkoutCompletionReportRepository(db)
    report = SubmitWorkoutCompletionReportUseCase(
        workout_repository,
        report_repository,
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        workout_id,
        body.difficulty_rating,
        body.mood_rating,
        body.comment,
        body.garmin_url,
        body.raw_report_text,
    )
    return _report_entity_to_response(report)


@router.get("/coach/athletes/{athlete_id}/training-plan", response_model=TrainingCalendarResponse)
def get_coach_athlete_training_plan(
    athlete_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    anchor_date: Annotated[date | None, Query()] = None,
) -> TrainingCalendarResponse:
    """View linked athlete training plan."""
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_TRAINING)
    calendar = _get_training_plan(
        db=db,
        access_guard=access_guard,
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        athlete_id=_parse_user_id(athlete_id),
        period=period,
        anchor_date=anchor_date,
    )
    return _calendar_to_response(calendar)


@router.get(
    "/coach/athletes/{athlete_id}/training-plan/text",
    response_model=TrainingPlanTextResponse,
)
def get_coach_athlete_training_plan_text(
    athlete_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    anchor_date: Annotated[date | None, Query()] = None,
) -> TrainingPlanTextResponse:
    """View linked athlete training plan as readable text. Coach only."""
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_TRAINING)
    calendar = _get_training_plan(
        db=db,
        access_guard=access_guard,
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        athlete_id=_parse_user_id(athlete_id),
        period=period,
        anchor_date=anchor_date,
    )
    export = format_training_calendar_as_text(calendar)
    return TrainingPlanTextResponse(
        anchor_date=calendar.anchor_date,
        period=calendar.period,
        text=export.text,
    )


@router.get("/athlete/training-plan", response_model=TrainingCalendarResponse)
def get_athlete_training_plan(
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    anchor_date: Annotated[date | None, Query()] = None,
) -> TrainingCalendarResponse:
    """View own training plan."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_TRAINING_PLAN)
    calendar = _get_training_plan(
        db=db,
        access_guard=access_guard,
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        athlete_id=authenticated_user.user.id,
        period=period,
        anchor_date=anchor_date,
    )
    return _calendar_to_response(calendar)


@router.get("/athlete/training-plan/text", response_model=TrainingPlanTextResponse)
def get_athlete_training_plan_text(
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    anchor_date: Annotated[date | None, Query()] = None,
) -> TrainingPlanTextResponse:
    """View own training plan as readable text. Athlete only."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_TRAINING_PLAN)
    calendar = _get_training_plan(
        db=db,
        access_guard=access_guard,
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        athlete_id=authenticated_user.user.id,
        period=period,
        anchor_date=anchor_date,
    )
    export = format_training_calendar_as_text(calendar)
    return TrainingPlanTextResponse(
        anchor_date=calendar.anchor_date,
        period=calendar.period,
        text=export.text,
    )


@router.get(
    "/coach/athletes/{athlete_id}/workout-reports",
    response_model=WorkoutReportSummaryResponse,
)
def list_coach_athlete_workout_reports(
    athlete_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    anchor_date: Annotated[date | None, Query()] = None,
) -> WorkoutReportSummaryResponse:
    """List completion reports for a linked athlete."""
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_TRAINING)
    summary = _list_workout_reports(
        db=db,
        access_guard=access_guard,
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        athlete_id=_parse_user_id(athlete_id),
        period=period,
        anchor_date=anchor_date,
    )
    return _reports_to_response(summary)


@router.get("/athlete/workout-reports", response_model=WorkoutReportSummaryResponse)
def list_athlete_workout_reports(
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: TrainingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    anchor_date: Annotated[date | None, Query()] = None,
) -> WorkoutReportSummaryResponse:
    """List own workout completion reports."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_TRAINING_PLAN)
    summary = _list_workout_reports(
        db=db,
        access_guard=access_guard,
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        athlete_id=authenticated_user.user.id,
        period=period,
        anchor_date=anchor_date,
    )
    return _reports_to_response(summary)
