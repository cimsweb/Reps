from application.dto.ai import AiProviderCredentials
from application.ports.ai_service import AIService
from domain.entities.agent_session_kind import AgentSessionKind
from domain.exceptions import AIServiceUnavailableError
from infrastructure.ai.openai_compatible_ai_service import OpenAICompatibleAIService
from infrastructure.ai.stub_ai_service import build_stub_ai_service
from infrastructure.config.ai_config import load_ai_api_key, load_ai_use_stub


def build_ai_service(
    session_kind: AgentSessionKind,
    *,
    credentials: AiProviderCredentials | None = None,
) -> AIService:
    if credentials is not None:
        return OpenAICompatibleAIService(
            api_key=credentials.api_key,
            base_url=credentials.base_url,
            model=credentials.model,
        )
    if load_ai_api_key() is not None:
        return OpenAICompatibleAIService()
    if load_ai_use_stub():
        return build_stub_ai_service(session_kind)
    raise AIServiceUnavailableError(
        "AI service is not configured. Set LLM access in settings (URL, model, API key)."
    )


def resolve_ai_credentials(
    *,
    api_url: str | None,
    api_key: str | None,
    model: str | None,
) -> AiProviderCredentials | None:
    """Build credentials from request fields; None means fall back to env/stub."""
    normalized_url = (api_url or "").strip()
    normalized_key = (api_key or "").strip()
    normalized_model = (model or "").strip()
    provided = [normalized_url, normalized_key, normalized_model]
    if not any(provided):
        return None
    if not all(provided):
        raise AIServiceUnavailableError(
            "Incomplete LLM settings. Set URL, model and API key in settings."
        )
    return AiProviderCredentials(
        api_key=normalized_key,
        base_url=normalized_url,
        model=normalized_model,
    )
