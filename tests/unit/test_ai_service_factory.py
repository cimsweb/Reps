import pytest

from domain.entities.agent_session_kind import AgentSessionKind
from domain.exceptions import AIServiceUnavailableError
from infrastructure.ai.ai_service_factory import build_ai_service


def test_build_ai_service_raises_without_key_or_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_USE_STUB", raising=False)

    with pytest.raises(AIServiceUnavailableError):
        build_ai_service(AgentSessionKind.PLAN_CREATION)


def test_build_ai_service_uses_stub_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.setenv("AI_USE_STUB", "true")

    service = build_ai_service(AgentSessionKind.PLAN_CREATION)

    assert service.__class__.__name__ == "StubAIService"
