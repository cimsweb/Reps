"""Tests for OpenAI-compatible AI service."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from application.dto.ai import ChatMessage
from domain.entities.agent_message_role import AgentMessageRole
from domain.exceptions import AIServiceUnavailableError
from infrastructure.ai.openai_compatible_ai_service import OpenAICompatibleAIService


def test_openai_compatible_service_raises_without_api_key() -> None:
    service = OpenAICompatibleAIService(api_key=None, base_url="https://example.com/v1", model="m")

    with pytest.raises(AIServiceUnavailableError, match="not configured"):
        asyncio.run(service.complete([]))


def test_openai_compatible_service_posts_chat_completions(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200

        def json(self) -> dict[str, object]:
            return {
                "model": "gpt-test",
                "choices": [{"message": {"content": '{"type":"question","text":"ok"}'}}],
            }

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            captured["timeout"] = kwargs.get("timeout")

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    service = OpenAICompatibleAIService(
        api_key="sk-test",
        base_url="https://llm.example/v1/",
        model="gpt-test",
        timeout_seconds=12,
    )
    completion = asyncio.run(
        service.complete(
            [ChatMessage(role=AgentMessageRole.USER, content="hello")],
        )
    )

    assert completion.content == '{"type":"question","text":"ok"}'
    assert completion.model == "gpt-test"
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["json"] == {
        "model": "gpt-test",
        "messages": [{"role": "user", "content": "hello"}],
    }
    assert captured["timeout"] == 12


def test_openai_compatible_service_maps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 401

        def json(self) -> dict[str, object]:
            return {"error": {"message": "Invalid API key"}}

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, *args: object, **kwargs: object):
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    service = OpenAICompatibleAIService(
        api_key="bad",
        base_url="https://llm.example/v1",
        model="gpt-test",
    )

    with pytest.raises(AIServiceUnavailableError, match="Invalid API key"):
        asyncio.run(service.complete([]))
