from dataclasses import dataclass

from domain.exceptions import InvalidConversationMessageContentError

_MAX_LENGTH = 5000


@dataclass(frozen=True, slots=True)
class ConversationMessageContent:
    """Validated human chat message body."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidConversationMessageContentError("Message content cannot be empty")
        if len(normalized) > _MAX_LENGTH:
            raise InvalidConversationMessageContentError(
                f"Message content must be at most {_MAX_LENGTH} characters"
            )
        object.__setattr__(self, "value", normalized)
