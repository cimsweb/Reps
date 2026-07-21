from __future__ import annotations

import httpx
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
    """OpenAI-compatible chat completions client."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else load_ai_api_key()
        self._base_url = (base_url if base_url is not None else load_ai_base_url()).rstrip("/")
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
        del response_schema
        if not self._api_key:
            raise AIServiceUnavailableError(
                "AI service is not configured. Set LLM access in settings (URL, model, API key)."
            )
        if not self._base_url or not self._model:
            raise AIServiceUnavailableError(
                "AI service is not configured. Set LLM access in settings (URL, model, API key)."
            )

        payload = {
            "model": self._model,
            "messages": [
                {"role": message.role.value, "content": message.content} for message in messages
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as error:
            raise AIServiceUnavailableError("AI provider request timed out") from error
        except httpx.HTTPError as error:
            raise AIServiceUnavailableError("AI provider request failed") from error

        if response.status_code >= 400:
            detail = _extract_error_detail(response)
            raise AIServiceUnavailableError(
                detail or f"AI provider returned HTTP {response.status_code}"
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise AIServiceUnavailableError("AI provider returned an invalid response") from error

        if not isinstance(content, str) or not content.strip():
            raise AIServiceUnavailableError("AI provider returned an empty response")

        model_name = data.get("model") if isinstance(data, dict) else None
        return ChatCompletion(
            content=content,
            model=model_name if isinstance(model_name, str) and model_name else self._model,
        )


def _extract_error_detail(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return None
