from dataclasses import dataclass

from domain.entities.agent_message_role import AgentMessageRole


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single message passed to the AI provider."""

    role: AgentMessageRole
    content: str


@dataclass(frozen=True, slots=True)
class ChatCompletion:
    """Raw completion returned by the AI provider."""

    content: str
    model: str
