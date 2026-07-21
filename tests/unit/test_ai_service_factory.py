import pytest

from application.dto.ai import AiProviderCredentials
from domain.entities.agent_session_kind import AgentSessionKind
from domain.exceptions import AIServiceUnavailableError
from infrastructure.ai.ai_service_factory import build_ai_service, resolve_ai_credentials


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


def test_build_ai_service_prefers_request_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_USE_STUB", "true")
    monkeypatch.delenv("AI_API_KEY", raising=False)

    service = build_ai_service(
        AgentSessionKind.PLAN_CREATION,
        credentials=AiProviderCredentials(
            api_key="sk-user",
            base_url="https://user.example/v1",
            model="user-model",
        ),
    )

    assert service.__class__.__name__ == "OpenAICompatibleAIService"
    assert service._api_key == "sk-user"
    assert service._base_url == "https://user.example/v1"
    assert service._model == "user-model"


def test_resolve_ai_credentials_requires_all_fields() -> None:
    assert resolve_ai_credentials(api_url=None, api_key=None, model=None) is None

    with pytest.raises(AIServiceUnavailableError, match="Incomplete"):
        resolve_ai_credentials(api_url="https://x", api_key="k", model=None)

    credentials = resolve_ai_credentials(
        api_url=" https://x/v1 ",
        api_key=" sk ",
        model=" m ",
    )
    assert credentials == AiProviderCredentials(
        api_key="sk",
        base_url="https://x/v1",
        model="m",
    )
