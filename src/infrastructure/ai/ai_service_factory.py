from application.ports.ai_service import AIService
from domain.entities.agent_session_kind import AgentSessionKind
from domain.exceptions import AIServiceUnavailableError
from infrastructure.ai.openai_compatible_ai_service import OpenAICompatibleAIService
from infrastructure.ai.stub_ai_service import build_stub_ai_service
from infrastructure.config.ai_config import load_ai_api_key, load_ai_use_stub


def build_ai_service(session_kind: AgentSessionKind) -> AIService:
    if load_ai_api_key() is not None:
        return OpenAICompatibleAIService()
    if load_ai_use_stub():
        return build_stub_ai_service(session_kind)
    raise AIServiceUnavailableError(
        "AI service is not configured. Set AI_API_KEY or AI_USE_STUB=true for development."
    )
