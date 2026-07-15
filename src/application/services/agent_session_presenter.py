from datetime import date

from application.dto.agent import AgentMessageView, AgentSessionView
from domain.entities.agent_message import AgentMessage
from domain.entities.agent_message_role import AgentMessageRole
from domain.entities.plan_scope import PlanScope
from domain.services.agent_assistant_reply import (
    AgentAssistantReply,
    AgentPlanDraftReply,
    AgentQuestionReply,
    AgentReportDraftReply,
    TrainingPlanDraft,
)
from domain.services.agent_session_rules import MAX_AGENT_MESSAGES_PER_SESSION
from domain.services.training_text_parsing import ReportDraft
from domain.value_objects.agent_session_id import AgentSessionId


def build_session_view(
    *,
    session_id: AgentSessionId,
    kind: str,
    status: str,
    messages: list[AgentMessage],
    latest_reply: AgentAssistantReply | None,
) -> AgentSessionView:
    message_views = tuple(
        AgentMessageView(
            role=message.role.value,
            content=message.content,
            sort_order=message.sort_order,
        )
        for message in messages
    )
    can_confirm = isinstance(latest_reply, (AgentPlanDraftReply, AgentReportDraftReply))
    return AgentSessionView(
        session_id=session_id,
        kind=kind,
        status=status,
        messages=message_views,
        messages_remaining=max(0, MAX_AGENT_MESSAGES_PER_SESSION - len(messages)),
        can_confirm=can_confirm,
        latest_reply=latest_reply,
    )


def extract_latest_plan_draft(messages: list[AgentMessage]) -> TrainingPlanDraft | None:
    for message in reversed(messages):
        if message.metadata is None or message.metadata.get("reply_type") != "plan_draft":
            continue
        draft_data = message.metadata.get("draft")
        if not isinstance(draft_data, dict):
            continue
        return TrainingPlanDraft(
            start_date=date.fromisoformat(str(draft_data["start_date"])),
            scope=PlanScope(str(draft_data["scope"])),
            raw_text=str(draft_data["raw_text"]) if draft_data.get("raw_text") else None,
        )
    return None


def extract_latest_report_draft(messages: list[AgentMessage]) -> ReportDraft | None:
    for message in reversed(messages):
        if message.metadata is None or message.metadata.get("reply_type") != "report_draft":
            continue
        draft_data = message.metadata.get("draft")
        if not isinstance(draft_data, dict):
            continue
        return ReportDraft(
            garmin_url=None,
            suggested_difficulty_rating=draft_data.get("suggested_difficulty_rating"),
            suggested_mood_rating=draft_data.get("suggested_mood_rating"),
            comment_body=draft_data.get("comment_body"),
            warnings=tuple(draft_data.get("warnings", [])),
        )
    return None


def rebuild_latest_reply(messages: list[AgentMessage]) -> AgentAssistantReply | None:
    for message in reversed(messages):
        if message.role is not AgentMessageRole.ASSISTANT:
            continue
        metadata = message.metadata or {}
        reply_type = metadata.get("reply_type")
        if reply_type == "question":
            return AgentQuestionReply(text=message.content)
        if reply_type == "plan_draft":
            plan_draft = extract_latest_plan_draft(messages)
            if plan_draft is not None:
                return AgentPlanDraftReply(draft=plan_draft)
        if reply_type == "report_draft":
            report_draft = extract_latest_report_draft(messages)
            if report_draft is not None:
                return AgentReportDraftReply(draft=report_draft)
    return None
