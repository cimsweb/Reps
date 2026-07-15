from dataclasses import dataclass
from datetime import datetime

from domain.entities.conversation import Conversation
from domain.entities.conversation_message import ConversationMessage


@dataclass(frozen=True, slots=True)
class ConversationMessageView:
    """Conversation message for API responses."""

    id: str
    conversation_id: str
    sender_id: str
    kind: str
    content: str
    sort_order: int
    read_at: datetime | None
    created_at: datetime
    is_mine: bool

    @classmethod
    def from_message(
        cls,
        message: ConversationMessage,
        *,
        actor_id: str,
    ) -> "ConversationMessageView":
        return cls(
            id=str(message.id.value),
            conversation_id=str(message.conversation_id.value),
            sender_id=str(message.sender_id.value),
            kind=message.kind.value,
            content=message.content,
            sort_order=message.sort_order,
            read_at=message.read_at,
            created_at=message.created_at,
            is_mine=str(message.sender_id.value) == actor_id,
        )


@dataclass(frozen=True, slots=True)
class ConversationSummaryView:
    """Conversation list item for API responses."""

    id: str
    coach_id: str
    athlete_id: str
    partner_id: str
    partner_email: str
    unread_count: int
    last_message_content: str | None
    last_message_at: datetime | None
    updated_at: datetime

    @classmethod
    def from_conversation(
        cls,
        conversation: Conversation,
        *,
        partner_id: str,
        partner_email: str,
        unread_count: int,
        last_message: ConversationMessage | None,
    ) -> "ConversationSummaryView":
        return cls(
            id=str(conversation.id.value),
            coach_id=str(conversation.coach_id.value),
            athlete_id=str(conversation.athlete_id.value),
            partner_id=partner_id,
            partner_email=partner_email,
            unread_count=unread_count,
            last_message_content=last_message.content if last_message else None,
            last_message_at=last_message.created_at if last_message else None,
            updated_at=conversation.updated_at,
        )


@dataclass(frozen=True, slots=True)
class PaginatedConversationMessages:
    """Paginated conversation messages."""

    items: tuple[ConversationMessageView, ...]
    total: int
