from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AgentMessageId:
    """Unique agent message identifier."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)
