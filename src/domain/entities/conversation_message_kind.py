from enum import StrEnum


class ConversationMessageKind(StrEnum):
    """Human chat message categories."""

    TEXT = "text"
    QUESTION = "question"
