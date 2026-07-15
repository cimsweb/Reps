from dataclasses import dataclass
from datetime import datetime

from domain.entities.agent_message_role import AgentMessageRole
from domain.value_objects.agent_message_id import AgentMessageId
from domain.value_objects.agent_session_id import AgentSessionId


@dataclass(frozen=True, slots=True)
class AgentMessage:
    """A single message within an agent dialog session."""

    id: AgentMessageId
    session_id: AgentSessionId
    role: AgentMessageRole
    content: str
    metadata: dict[str, object] | None
    sort_order: int
    created_at: datetime
