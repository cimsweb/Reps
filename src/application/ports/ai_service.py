from typing import Protocol

from pydantic import BaseModel

from application.dto.ai import ChatCompletion, ChatMessage


class AIService(Protocol):
    """Port for LLM completion calls."""

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: type[BaseModel] | None = None,
    ) -> ChatCompletion: ...
