from enum import StrEnum


class AgentSessionStatus(StrEnum):
    """Lifecycle state of an agent dialog session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
