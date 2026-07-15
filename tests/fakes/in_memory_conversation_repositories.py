"""In-memory conversation repository fakes for unit tests."""

from datetime import datetime

from domain.entities.conversation import Conversation
from domain.entities.conversation_message import ConversationMessage
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.user_id import UserId


class InMemoryConversationRepository:
    """Simple in-memory ConversationRepository for tests."""

    def __init__(self) -> None:
        self._by_id: dict[ConversationId, Conversation] = {}

    def save(self, conversation: Conversation) -> Conversation:
        self._by_id[conversation.id] = conversation
        return conversation

    def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        return self._by_id.get(conversation_id)

    def get_by_coach_and_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> Conversation | None:
        for conversation in self._by_id.values():
            if conversation.coach_id == coach_id and conversation.athlete_id == athlete_id:
                return conversation
        return None

    def list_by_coach(self, coach_id: UserId) -> list[Conversation]:
        return sorted(
            [
                conversation
                for conversation in self._by_id.values()
                if conversation.coach_id == coach_id
            ],
            key=lambda conversation: conversation.updated_at,
            reverse=True,
        )

    def list_by_athlete(self, athlete_id: UserId) -> list[Conversation]:
        return sorted(
            [
                conversation
                for conversation in self._by_id.values()
                if conversation.athlete_id == athlete_id
            ],
            key=lambda conversation: conversation.updated_at,
            reverse=True,
        )

    def touch_updated_at(
        self,
        conversation_id: ConversationId,
        *,
        updated_at: datetime,
    ) -> None:
        conversation = self._by_id.get(conversation_id)
        if conversation is None:
            return
        self._by_id[conversation_id] = Conversation(
            id=conversation.id,
            coach_id=conversation.coach_id,
            athlete_id=conversation.athlete_id,
            created_at=conversation.created_at,
            updated_at=updated_at,
        )


class InMemoryConversationMessageRepository:
    """Simple in-memory ConversationMessageRepository for tests."""

    def __init__(self) -> None:
        self._messages: list[ConversationMessage] = []

    def append(self, message: ConversationMessage) -> ConversationMessage:
        self._messages.append(message)
        return message

    def list_by_conversation(
        self,
        conversation_id: ConversationId,
        *,
        offset: int,
        limit: int,
    ) -> list[ConversationMessage]:
        items = [
            message for message in self._messages if message.conversation_id == conversation_id
        ]
        items.sort(key=lambda message: message.sort_order)
        return items[offset : offset + limit]

    def count_by_conversation(self, conversation_id: ConversationId) -> int:
        return sum(1 for message in self._messages if message.conversation_id == conversation_id)

    def get_latest_by_conversation(
        self,
        conversation_id: ConversationId,
    ) -> ConversationMessage | None:
        items = [
            message for message in self._messages if message.conversation_id == conversation_id
        ]
        if not items:
            return None
        return max(items, key=lambda message: message.sort_order)

    def count_unread_for_recipient(
        self,
        conversation_id: ConversationId,
        recipient_id: UserId,
    ) -> int:
        return sum(
            1
            for message in self._messages
            if message.conversation_id == conversation_id
            and message.sender_id != recipient_id
            and message.read_at is None
        )

    def mark_read_for_recipient(
        self,
        conversation_id: ConversationId,
        recipient_id: UserId,
        *,
        read_at: datetime,
    ) -> int:
        updated: list[ConversationMessage] = []
        marked_count = 0
        for message in self._messages:
            if (
                message.conversation_id == conversation_id
                and message.sender_id != recipient_id
                and message.read_at is None
            ):
                updated.append(
                    ConversationMessage(
                        id=message.id,
                        conversation_id=message.conversation_id,
                        sender_id=message.sender_id,
                        kind=message.kind,
                        content=message.content,
                        sort_order=message.sort_order,
                        read_at=read_at,
                        created_at=message.created_at,
                    )
                )
                marked_count += 1
            else:
                updated.append(message)
        self._messages = updated
        return marked_count

    def next_sort_order(self, conversation_id: ConversationId) -> int:
        items = [
            message for message in self._messages if message.conversation_id == conversation_id
        ]
        if not items:
            return 0
        return max(message.sort_order for message in items) + 1
