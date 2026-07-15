from typing import Protocol

from domain.entities.agent_message import AgentMessage
from domain.value_objects.agent_session_id import AgentSessionId


class AgentMessageRepository(Protocol):
    """Persistence contract for agent dialog messages."""

    def append(self, message: AgentMessage) -> AgentMessage:
        """Append a message to a session."""

    def list_by_session(self, session_id: AgentSessionId) -> list[AgentMessage]:
        """Return messages ordered by sort_order."""
