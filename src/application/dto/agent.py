"""Agent dialog read models."""

from dataclasses import dataclass

from domain.services.agent_assistant_reply import AgentAssistantReply
from domain.value_objects.agent_session_id import AgentSessionId


@dataclass(frozen=True, slots=True)
class AgentMessageView:
    role: str
    content: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class AgentSessionView:
    session_id: AgentSessionId
    kind: str
    status: str
    messages: tuple[AgentMessageView, ...]
    messages_remaining: int
    can_confirm: bool
    latest_reply: AgentAssistantReply | None
