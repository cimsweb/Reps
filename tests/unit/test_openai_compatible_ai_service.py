"""Unit tests for OpenAI-compatible AI service skeleton."""

import asyncio

import pytest

from domain.exceptions import AIServiceUnavailableError
from infrastructure.ai.openai_compatible_ai_service import OpenAICompatibleAIService


def test_openai_compatible_service_raises_without_api_key() -> None:
    service = OpenAICompatibleAIService(api_key=None)

    with pytest.raises(AIServiceUnavailableError, match="not configured"):
        asyncio.run(service.complete([]))


def test_openai_compatible_service_raises_not_implemented_with_key() -> None:
    service = OpenAICompatibleAIService(api_key="test-key")

    with pytest.raises(AIServiceUnavailableError, match="not implemented yet"):
        asyncio.run(service.complete([]))
