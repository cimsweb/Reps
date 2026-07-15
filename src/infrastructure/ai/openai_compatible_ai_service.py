from pydantic import BaseModel

from application.dto.ai import ChatCompletion, ChatMessage
from domain.exceptions import AIServiceUnavailableError
from infrastructure.config.ai_config import (
    load_ai_api_key,
    load_ai_base_url,
    load_ai_model,
    load_ai_timeout_seconds,
)


class OpenAICompatibleAIService:
    """Skeleton for OpenAI-compatible chat completions (implemented in MVP 2.2-002)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else load_ai_api_key()
        self._base_url = base_url if base_url is not None else load_ai_base_url()
        self._model = model if model is not None else load_ai_model()
        self._timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else load_ai_timeout_seconds()
        )

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: type[BaseModel] | None = None,
    ) -> ChatCompletion:
        del messages, response_schema
        if self._api_key is None:
            raise AIServiceUnavailableError("AI service is not configured (missing AI_API_KEY)")
        raise AIServiceUnavailableError(
            "OpenAI-compatible AI calls are not implemented yet (MVP 2.2-002)"
        )
