from enum import StrEnum


class AgentMessageRole(StrEnum):
    """Role of a message in an agent dialog."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
