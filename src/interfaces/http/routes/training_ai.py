from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.dto.agent import AgentSessionView
from application.security.training_access_guard import TrainingAccessGuard
from application.use_cases.agent_commands import (
    ConfirmPlanAgentDraftUseCase,
    ConfirmReportAgentDraftUseCase,
    SendPlanAgentMessageUseCase,
    SendReportAgentMessageUseCase,
    StartPlanAgentSessionUseCase,
    StartReportAgentSessionUseCase,
)
from application.use_cases.agent_queries import (
    GetActivePlanAgentSessionForAthleteUseCase,
    GetActiveReportAgentSessionForWorkoutUseCase,
    GetPlanAgentSessionUseCase,
    GetReportAgentSessionUseCase,
)
from domain.entities.plan_scope import PlanScope
from domain.services.agent_assistant_reply import (
    AgentPlanDraftReply,
    AgentQuestionReply,
    AgentReportDraftReply,
    TrainingPlanDraft,
)
from domain.services.authorization import Permission
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId
from infrastructure.ai.ai_service_factory import resolve_ai_credentials
from infrastructure.db.agent_repositories import (
    SqlAlchemyAgentMessageRepository,
    SqlAlchemyAgentSessionRepository,
)
from infrastructure.db.coaching_repositories import SqlAlchemyCoachAthleteLinkRepository
from infrastructure.db.training_repositories import (
    SqlAlchemyPlannedWorkoutRepository,
    SqlAlchemyTrainingPlanRepository,
    SqlAlchemyWorkoutCompletionReportRepository,
    SqlAlchemyWorkoutCycleRepository,
    SqlAlchemyWorkoutExerciseRepository,
)
from interfaces.http.dependencies import AuthorizationGuardDep, DbSession, get_bearer_token
from interfaces.http.routes.training import _plan_entity_to_response, _report_entity_to_response
from interfaces.http.schemas import (
    AgentMessageResponse,
    AgentPlanDraftReplyResponse,
    AgentQuestionReplyResponse,
    AgentReportDraftReplyResponse,
    AgentSessionResponse,
    ConfirmPlanAgentDraftRequest,
    ConfirmReportAgentDraftRequest,
    ParsedPlannedWorkoutDraftResponse,
    ParsedWorkoutCycleDraftResponse,
    ParsedWorkoutExerciseDraftResponse,
    SendAgentMessageRequest,
    StartPlanAgentSessionRequest,
    TrainingPlanDraftResponse,
    TrainingPlanResponse,
    WorkoutCompletionReportResponse,
)

router = APIRouter(tags=["training-ai"])


def _agent_use_case_dependencies(db: Session):
    access_guard = TrainingAccessGuard(SqlAlchemyCoachAthleteLinkRepository(db))
    session_repository = SqlAlchemyAgentSessionRepository(db)
    message_repository = SqlAlchemyAgentMessageRepository(db)
    plan_repository = SqlAlchemyTrainingPlanRepository(db)
    workout_repository = SqlAlchemyPlannedWorkoutRepository(db)
    cycle_repository = SqlAlchemyWorkoutCycleRepository(db)
    exercise_repository = SqlAlchemyWorkoutExerciseRepository(db)
    report_repository = SqlAlchemyWorkoutCompletionReportRepository(db)
    return {
        "access_guard": access_guard,
        "session_repository": session_repository,
        "message_repository": message_repository,
        "plan_repository": plan_repository,
        "workout_repository": workout_repository,
        "cycle_repository": cycle_repository,
        "exercise_repository": exercise_repository,
        "report_repository": report_repository,
    }


def _session_view_to_response(view: AgentSessionView) -> AgentSessionResponse:
    latest_reply: (
        AgentQuestionReplyResponse
        | AgentPlanDraftReplyResponse
        | AgentReportDraftReplyResponse
        | None
    ) = None
    if isinstance(view.latest_reply, AgentQuestionReply):
        latest_reply = AgentQuestionReplyResponse(text=view.latest_reply.text)
    elif isinstance(view.latest_reply, AgentPlanDraftReply) and view.latest_reply.draft is not None:
        plan_draft = view.latest_reply.draft
        workouts = []
        warnings: list[str] = []
        if plan_draft.parsed is not None:
            warnings = list(plan_draft.parsed.warnings)
            workouts = [
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
                for workout in plan_draft.parsed.workouts
            ]
        latest_reply = AgentPlanDraftReplyResponse(
            draft=TrainingPlanDraftResponse(
                start_date=plan_draft.start_date,
                scope=plan_draft.scope.value,
                raw_text=plan_draft.raw_text,
                warnings=warnings,
                workouts=workouts,
            )
        )
    elif (
        isinstance(view.latest_reply, AgentReportDraftReply) and view.latest_reply.draft is not None
    ):
        report_draft = view.latest_reply.draft
        latest_reply = AgentReportDraftReplyResponse(
            suggested_difficulty_rating=report_draft.suggested_difficulty_rating,
            suggested_mood_rating=report_draft.suggested_mood_rating,
            comment_body=report_draft.comment_body,
            garmin_url=str(report_draft.garmin_url) if report_draft.garmin_url else None,
            warnings=list(report_draft.warnings),
        )

    return AgentSessionResponse(
        session_id=str(view.session_id),
        kind=view.kind,
        status=view.status,
        messages=[
            AgentMessageResponse(
                role=message.role,
                content=message.content,
                sort_order=message.sort_order,
            )
            for message in view.messages
        ],
        messages_remaining=view.messages_remaining,
        can_confirm=view.can_confirm,
        latest_reply=latest_reply,
    )


@router.post(
    "/coach/athletes/{athlete_id}/training-plans/ai/sessions",
    response_model=AgentSessionResponse,
    status_code=201,
)
def start_plan_agent_session(
    athlete_id: UUID,
    request: StartPlanAgentSessionRequest,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    deps = _agent_use_case_dependencies(db)
    view = StartPlanAgentSessionUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        coach_id=authenticated_user.user.id,
        athlete_id=UserId(athlete_id),
        start_date=request.start_date,
        initial_brief=request.initial_brief,
        ai_credentials=resolve_ai_credentials(
            api_url=request.api_url,
            api_key=request.api_key,
            model=request.model,
        ),
    )
    return _session_view_to_response(view)


@router.post(
    "/coach/training-plans/ai/sessions/{session_id}/messages",
    response_model=AgentSessionResponse,
)
def send_plan_agent_message(
    session_id: UUID,
    request: SendAgentMessageRequest,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    deps = _agent_use_case_dependencies(db)
    view = SendPlanAgentMessageUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        coach_id=authenticated_user.user.id,
        session_id=AgentSessionId(session_id),
        content=request.content,
        ai_credentials=resolve_ai_credentials(
            api_url=request.api_url,
            api_key=request.api_key,
            model=request.model,
        ),
    )
    return _session_view_to_response(view)


@router.get(
    "/coach/training-plans/ai/sessions/{session_id}",
    response_model=AgentSessionResponse,
)
def get_plan_agent_session(
    session_id: UUID,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_TRAINING)
    deps = _agent_use_case_dependencies(db)
    view = GetPlanAgentSessionUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        coach_id=authenticated_user.user.id,
        session_id=AgentSessionId(session_id),
    )
    return _session_view_to_response(view)


@router.get(
    "/coach/athletes/{athlete_id}/training-plans/ai/sessions/active",
    response_model=AgentSessionResponse,
)
def get_active_plan_agent_session_for_athlete(
    athlete_id: UUID,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_TRAINING)
    deps = _agent_use_case_dependencies(db)
    view = GetActivePlanAgentSessionForAthleteUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        coach_id=authenticated_user.user.id,
        athlete_id=UserId(athlete_id),
    )
    return _session_view_to_response(view)


@router.post(
    "/coach/training-plans/ai/sessions/{session_id}/confirm",
    response_model=TrainingPlanResponse,
    status_code=201,
)
def confirm_plan_agent_draft(
    session_id: UUID,
    request: ConfirmPlanAgentDraftRequest,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> TrainingPlanResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_TRAINING_PLANS)
    deps = _agent_use_case_dependencies(db)
    draft_override = None
    if request.start_date is not None:
        draft_override = TrainingPlanDraft(
            start_date=request.start_date,
            scope=PlanScope(request.scope) if request.scope else PlanScope.WEEK,
            raw_text=request.raw_text,
        )
    result = ConfirmPlanAgentDraftUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        plan_repository=deps["plan_repository"],
        workout_repository=deps["workout_repository"],
        cycle_repository=deps["cycle_repository"],
        exercise_repository=deps["exercise_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        coach_id=authenticated_user.user.id,
        session_id=AgentSessionId(session_id),
        draft_override=draft_override,
    )
    return _plan_entity_to_response(result.plan, db)


@router.post(
    "/athlete/planned-workouts/{planned_workout_id}/report/ai/sessions",
    response_model=AgentSessionResponse,
    status_code=201,
)
def start_report_agent_session(
    planned_workout_id: UUID,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.SUBMIT_WORKOUT_REPORT)
    deps = _agent_use_case_dependencies(db)
    view = StartReportAgentSessionUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        workout_repository=deps["workout_repository"],
        cycle_repository=deps["cycle_repository"],
        exercise_repository=deps["exercise_repository"],
        report_repository=deps["report_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        athlete_id=authenticated_user.user.id,
        planned_workout_id=PlannedWorkoutId(planned_workout_id),
    )
    return _session_view_to_response(view)


@router.get(
    "/athlete/report/ai/sessions/{session_id}",
    response_model=AgentSessionResponse,
)
def get_report_agent_session(
    session_id: UUID,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.SUBMIT_WORKOUT_REPORT)
    deps = _agent_use_case_dependencies(db)
    view = GetReportAgentSessionUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        athlete_id=authenticated_user.user.id,
        session_id=AgentSessionId(session_id),
    )
    return _session_view_to_response(view)


@router.get(
    "/athlete/planned-workouts/{planned_workout_id}/report/ai/sessions/active",
    response_model=AgentSessionResponse,
)
def get_active_report_agent_session_for_workout(
    planned_workout_id: UUID,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.SUBMIT_WORKOUT_REPORT)
    deps = _agent_use_case_dependencies(db)
    view = GetActiveReportAgentSessionForWorkoutUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        workout_repository=deps["workout_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        athlete_id=authenticated_user.user.id,
        planned_workout_id=PlannedWorkoutId(planned_workout_id),
    )
    return _session_view_to_response(view)


@router.post(
    "/athlete/report/ai/sessions/{session_id}/messages",
    response_model=AgentSessionResponse,
)
def send_report_agent_message(
    session_id: UUID,
    request: SendAgentMessageRequest,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> AgentSessionResponse:
    authenticated_user = guard.authorize(token, Permission.SUBMIT_WORKOUT_REPORT)
    deps = _agent_use_case_dependencies(db)
    view = SendReportAgentMessageUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        workout_repository=deps["workout_repository"],
        cycle_repository=deps["cycle_repository"],
        exercise_repository=deps["exercise_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        athlete_id=authenticated_user.user.id,
        session_id=AgentSessionId(session_id),
        content=request.content,
        ai_credentials=resolve_ai_credentials(
            api_url=request.api_url,
            api_key=request.api_key,
            model=request.model,
        ),
    )
    return _session_view_to_response(view)


@router.post(
    "/athlete/report/ai/sessions/{session_id}/confirm",
    response_model=WorkoutCompletionReportResponse,
    status_code=201,
)
def confirm_report_agent_draft(
    session_id: UUID,
    request: ConfirmReportAgentDraftRequest,
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
    guard: AuthorizationGuardDep,
) -> WorkoutCompletionReportResponse:
    authenticated_user = guard.authorize(token, Permission.SUBMIT_WORKOUT_REPORT)
    deps = _agent_use_case_dependencies(db)
    result = ConfirmReportAgentDraftUseCase(
        session_repository=deps["session_repository"],
        message_repository=deps["message_repository"],
        workout_repository=deps["workout_repository"],
        report_repository=deps["report_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        athlete_id=authenticated_user.user.id,
        session_id=AgentSessionId(session_id),
        difficulty_rating=request.difficulty_rating,
        mood_rating=request.mood_rating,
        comment=request.comment,
        garmin_url=request.garmin_url,
        raw_report_text=request.raw_report_text,
    )
    return _report_entity_to_response(result.report)
