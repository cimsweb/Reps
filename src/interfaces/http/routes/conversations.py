from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.dto.conversation import ConversationMessageView, ConversationSummaryView
from application.security.coaching_access_guard import CoachingAccessGuard
from application.use_cases.conversation_commands import (
    MarkConversationReadUseCase,
    SendAthleteConversationMessageUseCase,
    SendCoachConversationMessageUseCase,
)
from application.use_cases.conversation_queries import (
    ListAthleteConversationsUseCase,
    ListCoachConversationsUseCase,
    ListConversationMessagesUseCase,
)
from domain.entities.conversation_message_kind import ConversationMessageKind
from domain.entities.role import Role
from domain.services.authorization import Permission
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.pagination import PageRequest
from domain.value_objects.user_id import UserId
from infrastructure.db.coaching_repositories import SqlAlchemyCoachAthleteLinkRepository
from infrastructure.db.conversation_repositories import (
    SqlAlchemyConversationMessageRepository,
    SqlAlchemyConversationRepository,
)
from infrastructure.db.repositories import SqlAlchemyUserRepository
from interfaces.http.dependencies import AuthorizationGuardDep, DbSession, get_bearer_token
from interfaces.http.schemas import (
    ConversationListResponse,
    ConversationMessageListResponse,
    ConversationMessageResponse,
    ConversationSummaryResponse,
    MarkConversationReadResponse,
    SendConversationMessageRequest,
)

router = APIRouter(tags=["conversations"])


def _conversation_dependencies(db):
    link_repository = SqlAlchemyCoachAthleteLinkRepository(db)
    return {
        "conversation_repository": SqlAlchemyConversationRepository(db),
        "message_repository": SqlAlchemyConversationMessageRepository(db),
        "user_repository": SqlAlchemyUserRepository(db),
        "access_guard": CoachingAccessGuard(link_repository),
    }


def _summary_to_response(view: ConversationSummaryView) -> ConversationSummaryResponse:
    return ConversationSummaryResponse(
        id=view.id,
        coach_id=view.coach_id,
        athlete_id=view.athlete_id,
        partner_id=view.partner_id,
        partner_email=view.partner_email,
        unread_count=view.unread_count,
        last_message_content=view.last_message_content,
        last_message_at=view.last_message_at,
        updated_at=view.updated_at,
    )


def _message_to_response(view: ConversationMessageView) -> ConversationMessageResponse:
    return ConversationMessageResponse(
        id=view.id,
        conversation_id=view.conversation_id,
        sender_id=view.sender_id,
        kind=view.kind,
        content=view.content,
        sort_order=view.sort_order,
        read_at=view.read_at,
        created_at=view.created_at,
        is_mine=view.is_mine,
    )


@router.get("/coach/conversations", response_model=ConversationListResponse)
def list_coach_conversations(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> ConversationListResponse:
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    deps = _conversation_dependencies(db)
    views = ListCoachConversationsUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        user_repository=deps["user_repository"],
    ).execute(authenticated_user.user.id, authenticated_user.user.role)
    return ConversationListResponse(items=[_summary_to_response(view) for view in views])


@router.get("/athlete/conversations", response_model=ConversationListResponse)
def list_athlete_conversations(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> ConversationListResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    deps = _conversation_dependencies(db)
    views = ListAthleteConversationsUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        user_repository=deps["user_repository"],
    ).execute(authenticated_user.user.id, authenticated_user.user.role)
    return ConversationListResponse(items=[_summary_to_response(view) for view in views])


@router.get(
    "/coach/conversations/{conversation_id}/messages",
    response_model=ConversationMessageListResponse,
)
def list_coach_conversation_messages(
    conversation_id: UUID,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ConversationMessageListResponse:
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    deps = _conversation_dependencies(db)
    page = ListConversationMessagesUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        conversation_id=ConversationId(conversation_id),
        page=PageRequest(offset=offset, limit=limit),
    )
    return ConversationMessageListResponse(
        items=[_message_to_response(item) for item in page.items],
        total=page.total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/athlete/conversations/{conversation_id}/messages",
    response_model=ConversationMessageListResponse,
)
def list_athlete_conversation_messages(
    conversation_id: UUID,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ConversationMessageListResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    deps = _conversation_dependencies(db)
    page = ListConversationMessagesUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        conversation_id=ConversationId(conversation_id),
        page=PageRequest(offset=offset, limit=limit),
    )
    return ConversationMessageListResponse(
        items=[_message_to_response(item) for item in page.items],
        total=page.total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/coach/athletes/{athlete_id}/messages",
    response_model=ConversationMessageResponse,
    status_code=201,
)
def send_coach_message(
    athlete_id: UUID,
    body: SendConversationMessageRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> ConversationMessageResponse:
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    deps = _conversation_dependencies(db)
    view = SendCoachConversationMessageUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        coach_id=authenticated_user.user.id,
        coach_role=Role.COACH,
        athlete_id=UserId(athlete_id),
        content=body.content,
        kind=ConversationMessageKind(body.kind),
    )
    return _message_to_response(view)


@router.post(
    "/athlete/coaches/{coach_id}/messages",
    response_model=ConversationMessageResponse,
    status_code=201,
)
def send_athlete_message(
    coach_id: UUID,
    body: SendConversationMessageRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> ConversationMessageResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    deps = _conversation_dependencies(db)
    view = SendAthleteConversationMessageUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        athlete_id=authenticated_user.user.id,
        athlete_role=Role.ATHLETE,
        coach_id=UserId(coach_id),
        content=body.content,
        kind=ConversationMessageKind(body.kind),
    )
    return _message_to_response(view)


@router.post(
    "/coach/conversations/{conversation_id}/read",
    response_model=MarkConversationReadResponse,
)
def mark_coach_conversation_read(
    conversation_id: UUID,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> MarkConversationReadResponse:
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    deps = _conversation_dependencies(db)
    marked_count = MarkConversationReadUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        conversation_id=ConversationId(conversation_id),
    )
    return MarkConversationReadResponse(marked_count=marked_count)


@router.post(
    "/athlete/conversations/{conversation_id}/read",
    response_model=MarkConversationReadResponse,
)
def mark_athlete_conversation_read(
    conversation_id: UUID,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> MarkConversationReadResponse:
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    deps = _conversation_dependencies(db)
    marked_count = MarkConversationReadUseCase(
        conversation_repository=deps["conversation_repository"],
        message_repository=deps["message_repository"],
        access_guard=deps["access_guard"],
    ).execute(
        actor_id=authenticated_user.user.id,
        actor_role=authenticated_user.user.role,
        conversation_id=ConversationId(conversation_id),
    )
    return MarkConversationReadResponse(marked_count=marked_count)
