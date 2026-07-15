from datetime import datetime
from typing import Protocol

from domain.entities.conversation_message import ConversationMessage
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.user_id import UserId


class ConversationMessageRepository(Protocol):
    """Persistence contract for conversation messages."""

    def append(self, message: ConversationMessage) -> ConversationMessage:
        """Persist a new message."""

    def list_by_conversation(
        self,
        conversation_id: ConversationId,
        *,
        offset: int,
        limit: int,
    ) -> list[ConversationMessage]:
        """Return messages ordered by sort_order ascending."""

    def count_by_conversation(self, conversation_id: ConversationId) -> int:
        """Return total message count for a conversation."""

    def get_latest_by_conversation(
        self,
        conversation_id: ConversationId,
    ) -> ConversationMessage | None:
        """Return the most recent message in a conversation."""

    def count_unread_for_recipient(
        self,
        conversation_id: ConversationId,
        recipient_id: UserId,
    ) -> int:
        """Return unread messages sent by the other party."""

    def mark_read_for_recipient(
        self,
        conversation_id: ConversationId,
        recipient_id: UserId,
        *,
        read_at: datetime,
    ) -> int:
        """Mark incoming messages as read for the recipient."""

    def next_sort_order(self, conversation_id: ConversationId) -> int:
        """Return the next sort order for a conversation."""
