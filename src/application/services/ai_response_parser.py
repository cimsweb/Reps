import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from application.dto.ai_responses import (
    AIPlanDraftPayload,
    AIQuestionPayload,
    AIReportDraftPayload,
)
from domain.entities.plan_scope import PlanScope
from domain.exceptions import AIResponseInvalidError
from domain.services.agent_assistant_reply import (
    AgentAssistantReply,
    AgentPlanDraftReply,
    AgentQuestionReply,
    AgentReportDraftReply,
    TrainingPlanDraft,
)
from domain.services.training_text_parsing import ReportDraft
from domain.value_objects.garmin_report_url import GarminReportUrl


def parse_plan_agent_response(raw_content: str) -> AgentAssistantReply:
    return _parse_payload(raw_content, _to_plan_reply)


def parse_report_agent_response(raw_content: str) -> AgentAssistantReply:
    return _parse_payload(raw_content, _to_report_reply)


def _parse_payload(
    raw_content: str,
    converter: Callable[[dict[str, object]], AgentAssistantReply],
) -> AgentAssistantReply:
    try:
        payload = json.loads(_extract_json_object(raw_content))
        if not isinstance(payload, dict):
            raise AIResponseInvalidError("AI response must be a JSON object")
        return converter(payload)
    except (json.JSONDecodeError, ValidationError, KeyError, ValueError) as error:
        raise AIResponseInvalidError(f"AI returned invalid response: {error}") from error


def _extract_json_object(raw_content: str) -> str:
    stripped = raw_content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped


def _to_plan_reply(payload: dict[str, object]) -> AgentAssistantReply:
    response_type = payload.get("type")
    if response_type == "question":
        question = AIQuestionPayload.model_validate(payload)
        return AgentQuestionReply(text=question.text)
    if response_type == "plan_draft":
        draft_payload = AIPlanDraftPayload.model_validate(payload)
        return AgentPlanDraftReply(
            draft=TrainingPlanDraft(
                start_date=draft_payload.start_date,
                scope=PlanScope(draft_payload.scope),
                raw_text=draft_payload.raw_text,
            )
        )
    raise AIResponseInvalidError("Unexpected plan agent response type")


def _to_report_reply(payload: dict[str, object]) -> AgentAssistantReply:
    response_type = payload.get("type")
    if response_type == "question":
        question = AIQuestionPayload.model_validate(payload)
        return AgentQuestionReply(text=question.text)
    if response_type == "report_draft":
        draft_payload = AIReportDraftPayload.model_validate(payload)
        garmin_url = None
        if draft_payload.garmin_url:
            garmin_url = GarminReportUrl(draft_payload.garmin_url.strip())
        return AgentReportDraftReply(
            draft=ReportDraft(
                garmin_url=garmin_url,
                suggested_difficulty_rating=draft_payload.suggested_difficulty_rating,
                suggested_mood_rating=draft_payload.suggested_mood_rating,
                comment_body=draft_payload.comment_body,
            )
        )
    raise AIResponseInvalidError("Unexpected report agent response type")
