import asyncio
import hashlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from application.dto.ai import ChatCompletion, ChatMessage
from application.ports.ai_service import AIService
from application.services.ai_response_parser import (
    parse_plan_agent_response,
    parse_report_agent_response,
)
from domain.entities.agent_message import AgentMessage
from domain.entities.agent_message_role import AgentMessageRole
from domain.entities.agent_session import AgentSession
from domain.entities.agent_session_kind import AgentSessionKind
from domain.entities.agent_session_status import AgentSessionStatus
from domain.exceptions import (
    AgentSessionExpiredError,
    AgentSessionMessageLimitError,
    AgentSessionNotActiveError,
    AgentSessionNotFoundError,
    AIResponseInvalidError,
    TrainingAccessDeniedError,
)
from domain.repositories.agent_message_repository import AgentMessageRepository
from domain.repositories.agent_session_repository import AgentSessionRepository
from domain.services.agent_assistant_reply import (
    AgentAssistantReply,
    AgentPlanDraftReply,
    AgentQuestionReply,
    AgentReportDraftReply,
    TrainingPlanDraft,
)
from domain.services.agent_session_rules import (
    AGENT_SESSION_EXPIRY_HOURS,
    MAX_AGENT_MESSAGES_PER_SESSION,
)
from domain.value_objects.agent_message_id import AgentMessageId
from domain.value_objects.user_id import UserId
from infrastructure.ai.prompt_loader import render_prompt_template
from infrastructure.parsing.rule_based_training_text_parser import RuleBasedTrainingTextParser


def run_ai_completion(
    ai_service: AIService,
    messages: list[ChatMessage],
) -> ChatCompletion:
    return asyncio.run(ai_service.complete(messages))


def invoke_plan_agent_ai(
    ai_service: AIService,
    messages: list[ChatMessage],
) -> AgentAssistantReply:
    return _invoke_with_retry(ai_service, messages, parse_plan_agent_response)


def invoke_report_agent_ai(
    ai_service: AIService,
    messages: list[ChatMessage],
) -> AgentAssistantReply:
    return _invoke_with_retry(ai_service, messages, parse_report_agent_response)


def _invoke_with_retry(
    ai_service: AIService,
    messages: list[ChatMessage],
    parser: Callable[[str], AgentAssistantReply],
) -> AgentAssistantReply:
    last_error: AIResponseInvalidError | None = None
    for _ in range(2):
        completion = run_ai_completion(ai_service, messages)
        try:
            return parser(completion.content)
        except AIResponseInvalidError as error:
            last_error = error
    assert last_error is not None
    raise last_error


def ensure_session_active(session: AgentSession) -> None:
    if session.status is not AgentSessionStatus.ACTIVE:
        raise AgentSessionNotActiveError(f"Agent session is not active: {session.id}")


def ensure_session_not_expired(session: AgentSession, *, now: datetime | None = None) -> None:
    current_time = now or datetime.now(UTC)
    expiry = session.updated_at + timedelta(hours=AGENT_SESSION_EXPIRY_HOURS)
    if current_time > expiry:
        raise AgentSessionExpiredError(f"Agent session expired: {session.id}")


def ensure_message_limit(messages: list[AgentMessage]) -> None:
    if len(messages) >= MAX_AGENT_MESSAGES_PER_SESSION:
        raise AgentSessionMessageLimitError(
            f"Agent session reached message limit of {MAX_AGENT_MESSAGES_PER_SESSION}"
        )


def load_coach_plan_session(
    session_repository: AgentSessionRepository,
    session_id,
    coach_id: UserId,
) -> AgentSession:
    session = _load_coach_owned_plan_session(session_repository, session_id, coach_id)
    ensure_session_active(session)
    ensure_session_not_expired(session)
    return session


def load_coach_plan_session_for_view(
    session_repository: AgentSessionRepository,
    session_id,
    coach_id: UserId,
) -> AgentSession:
    session = _load_coach_owned_plan_session(session_repository, session_id, coach_id)
    if session.status is AgentSessionStatus.ACTIVE:
        ensure_session_not_expired(session)
    return session


def load_athlete_report_session(
    session_repository: AgentSessionRepository,
    session_id,
    athlete_id: UserId,
) -> AgentSession:
    session = _load_athlete_owned_report_session(session_repository, session_id, athlete_id)
    ensure_session_active(session)
    ensure_session_not_expired(session)
    return session


def load_athlete_report_session_for_view(
    session_repository: AgentSessionRepository,
    session_id,
    athlete_id: UserId,
) -> AgentSession:
    session = _load_athlete_owned_report_session(session_repository, session_id, athlete_id)
    if session.status is AgentSessionStatus.ACTIVE:
        ensure_session_not_expired(session)
    return session


def _load_coach_owned_plan_session(
    session_repository: AgentSessionRepository,
    session_id,
    coach_id: UserId,
) -> AgentSession:
    session = session_repository.get_by_id(session_id)
    if session is None or session.kind is not AgentSessionKind.PLAN_CREATION:
        raise AgentSessionNotFoundError(f"Agent session not found: {session_id}")
    if session.coach_id != coach_id:
        raise TrainingAccessDeniedError("Coach cannot access this agent session")
    return session


def _load_athlete_owned_report_session(
    session_repository: AgentSessionRepository,
    session_id,
    athlete_id: UserId,
) -> AgentSession:
    session = session_repository.get_by_id(session_id)
    if session is None or session.kind is not AgentSessionKind.REPORT_ASSISTANCE:
        raise AgentSessionNotFoundError(f"Agent session not found: {session_id}")
    if session.athlete_id != athlete_id:
        raise TrainingAccessDeniedError("Athlete cannot access this agent session")
    return session


def touch_session(session: AgentSession, *, now: datetime | None = None) -> AgentSession:
    current_time = now or datetime.now(UTC)
    return AgentSession(
        id=session.id,
        kind=session.kind,
        coach_id=session.coach_id,
        athlete_id=session.athlete_id,
        planned_workout_id=session.planned_workout_id,
        status=session.status,
        start_date=session.start_date,
        created_at=session.created_at,
        updated_at=current_time,
    )


def complete_session(session: AgentSession, *, now: datetime | None = None) -> AgentSession:
    touched = touch_session(session, now=now)
    return AgentSession(
        id=touched.id,
        kind=touched.kind,
        coach_id=touched.coach_id,
        athlete_id=touched.athlete_id,
        planned_workout_id=touched.planned_workout_id,
        status=AgentSessionStatus.COMPLETED,
        start_date=touched.start_date,
        created_at=touched.created_at,
        updated_at=touched.updated_at,
    )


def append_user_message(
    message_repository: AgentMessageRepository,
    *,
    session: AgentSession,
    content: str,
    sort_order: int,
    now: datetime | None = None,
) -> AgentMessage:
    current_time = now or datetime.now(UTC)
    return message_repository.append(
        AgentMessage(
            id=AgentMessageId(uuid4()),
            session_id=session.id,
            role=AgentMessageRole.USER,
            content=content.strip(),
            metadata=None,
            sort_order=sort_order,
            created_at=current_time,
        )
    )


def append_assistant_message(
    message_repository: AgentMessageRepository,
    *,
    session: AgentSession,
    reply: AgentAssistantReply,
    sort_order: int,
    now: datetime | None = None,
) -> AgentMessage:
    current_time = now or datetime.now(UTC)
    content, metadata = _assistant_reply_to_storage(reply)
    return message_repository.append(
        AgentMessage(
            id=AgentMessageId(uuid4()),
            session_id=session.id,
            role=AgentMessageRole.ASSISTANT,
            content=content,
            metadata=metadata,
            sort_order=sort_order,
            created_at=current_time,
        )
    )


def build_chat_messages(
    *,
    system_prompt: str,
    history: list[AgentMessage],
) -> list[ChatMessage]:
    messages = [ChatMessage(role=AgentMessageRole.SYSTEM, content=system_prompt)]
    for message in history:
        messages.append(ChatMessage(role=message.role, content=message.content))
    return messages


def build_plan_system_prompt(*, athlete_id: UserId, start_date) -> str:
    return render_prompt_template(
        "coach_plan_system.md",
        athlete_id=str(athlete_id.value),
        start_date=start_date.isoformat(),
    )


def build_report_system_prompt(*, workout_context: str) -> str:
    return render_prompt_template(
        "athlete_report_system.md",
        workout_context=workout_context,
    )


def enrich_plan_draft_reply(reply: AgentAssistantReply, *, start_date) -> AgentAssistantReply:
    if not isinstance(reply, AgentPlanDraftReply) or reply.draft is None:
        return reply
    draft = reply.draft
    parser = RuleBasedTrainingTextParser()
    parsed = (
        parser.parse_day(text=draft.raw_text or "", planned_date=draft.start_date)
        if draft.scope.value == "day"
        else parser.parse_week(text=draft.raw_text or "", start_date=draft.start_date)
    )
    enriched = TrainingPlanDraft(
        start_date=draft.start_date or start_date,
        scope=draft.scope,
        raw_text=draft.raw_text,
        parsed=parsed,
    )
    return AgentPlanDraftReply(draft=enriched)


def log_ai_event(
    logger: logging.Logger,
    event: str,
    *,
    session_id: str,
    kind: str,
    content: str | None = None,
    user_id: str | None = None,
) -> None:
    extra: dict[str, object] = {
        "session_id": session_id,
        "kind": kind,
    }
    if user_id is not None:
        extra["user_id"] = user_id
    if content is not None:
        extra["content_len"] = len(content)
        extra["content_hash"] = hashlib.sha256(content.encode()).hexdigest()[:12]
    logger.info(event, extra=extra)


def _assistant_reply_to_storage(reply: AgentAssistantReply) -> tuple[str, dict[str, object]]:
    if isinstance(reply, AgentQuestionReply):
        return reply.text, {"reply_type": "question"}
    if isinstance(reply, AgentPlanDraftReply):
        plan_draft = reply.draft
        assert plan_draft is not None
        warnings = list(plan_draft.parsed.warnings) if plan_draft.parsed else []
        return (
            plan_draft.raw_text or "",
            {
                "reply_type": "plan_draft",
                "draft": {
                    "start_date": plan_draft.start_date.isoformat(),
                    "scope": plan_draft.scope.value,
                    "raw_text": plan_draft.raw_text,
                    "warnings": warnings,
                },
            },
        )
    if isinstance(reply, AgentReportDraftReply):
        report_draft = reply.draft
        assert report_draft is not None
        return (
            report_draft.comment_body or "",
            {
                "reply_type": "report_draft",
                "draft": {
                    "suggested_difficulty_rating": report_draft.suggested_difficulty_rating,
                    "suggested_mood_rating": report_draft.suggested_mood_rating,
                    "comment_body": report_draft.comment_body,
                    "garmin_url": str(report_draft.garmin_url) if report_draft.garmin_url else None,
                    "warnings": list(report_draft.warnings),
                },
            },
        )
    raise AIResponseInvalidError("Unsupported assistant reply type")
