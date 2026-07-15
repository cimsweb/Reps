from dataclasses import dataclass
from datetime import datetime

from domain.entities.conversation_message_kind import ConversationMessageKind
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.conversation_message_id import ConversationMessageId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """A single message in a coach-athlete conversation."""

    id: ConversationMessageId
    conversation_id: ConversationId
    sender_id: UserId
    kind: ConversationMessageKind
    content: str
    sort_order: int
    read_at: datetime | None
    created_at: datetime
