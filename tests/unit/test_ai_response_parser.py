"""Unit tests for AI response parser."""

import pytest

from application.services.ai_response_parser import (
    parse_plan_agent_response,
    parse_report_agent_response,
)
from domain.exceptions import AIResponseInvalidError
from domain.services.agent_assistant_reply import (
    AgentPlanDraftReply,
    AgentQuestionReply,
    AgentReportDraftReply,
)


def test_parse_plan_question_response() -> None:
    reply = parse_plan_agent_response(
        '{"type": "question", "text": "Какой объём длительного бега?"}'
    )
    assert isinstance(reply, AgentQuestionReply)
    assert "объём" in reply.text


def test_parse_plan_draft_response() -> None:
    reply = parse_plan_agent_response(
        '{"type": "plan_draft", "start_date": "2024-06-08", "scope": "week", "raw_text": "8 Июня"}'
    )
    assert isinstance(reply, AgentPlanDraftReply)
    assert reply.draft is not None
    assert reply.draft.scope.value == "week"


def test_parse_report_draft_response() -> None:
    reply = parse_report_agent_response(
        '{"type": "report_draft", "suggested_difficulty_rating": 5, "suggested_mood_rating": 7}'
    )
    assert isinstance(reply, AgentReportDraftReply)
    assert reply.draft is not None
    assert reply.draft.suggested_difficulty_rating == 5


def test_parse_invalid_json_raises() -> None:
    with pytest.raises(AIResponseInvalidError):
        parse_plan_agent_response("not json")
