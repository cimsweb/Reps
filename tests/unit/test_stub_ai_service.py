"""Unit tests for StubAIService."""

import asyncio
import json

from application.dto.ai import ChatMessage
from domain.entities.agent_message_role import AgentMessageRole
from domain.entities.agent_session_kind import AgentSessionKind
from infrastructure.ai.stub_ai_service import StubAIService


def test_stub_plan_dialog_returns_question_then_draft() -> None:
    service = StubAIService(session_kind=AgentSessionKind.PLAN_CREATION)
    messages = [ChatMessage(role=AgentMessageRole.USER, content="бег зал бег")]

    first = asyncio.run(service.complete(messages))
    messages.append(ChatMessage(role=AgentMessageRole.ASSISTANT, content="question"))
    messages.append(ChatMessage(role=AgentMessageRole.USER, content="120"))
    second = asyncio.run(service.complete(messages))

    first_payload = json.loads(first.content)
    second_payload = json.loads(second.content)

    assert first_payload["type"] == "question"
    assert second_payload["type"] == "plan_draft"
    assert second_payload["scope"] == "week"


def test_stub_report_dialog_returns_questions_then_draft() -> None:
    service = StubAIService(session_kind=AgentSessionKind.REPORT_ASSISTANCE)
    messages = [ChatMessage(role=AgentMessageRole.USER, content="нагрузка 5")]

    first = asyncio.run(service.complete(messages))
    messages.extend(
        [
            ChatMessage(role=AgentMessageRole.ASSISTANT, content="q1"),
            ChatMessage(role=AgentMessageRole.USER, content="интервалы"),
        ]
    )
    second = asyncio.run(service.complete(messages))
    messages.extend(
        [
            ChatMessage(role=AgentMessageRole.ASSISTANT, content="q2"),
            ChatMessage(role=AgentMessageRole.USER, content="нормально"),
        ]
    )
    third = asyncio.run(service.complete(messages))

    assert json.loads(first.content)["type"] == "question"
    assert json.loads(second.content)["type"] == "question"
    assert json.loads(third.content)["type"] == "report_draft"
