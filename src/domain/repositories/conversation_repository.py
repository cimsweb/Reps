from datetime import datetime
from typing import Protocol

from domain.entities.conversation import Conversation
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.user_id import UserId


class ConversationRepository(Protocol):
    """Persistence contract for coach-athlete conversations."""

    def save(self, conversation: Conversation) -> Conversation:
        """Persist a conversation."""

    def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        """Return conversation by id."""

    def get_by_coach_and_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> Conversation | None:
        """Return conversation for a coach-athlete pair."""

    def list_by_coach(self, coach_id: UserId) -> list[Conversation]:
        """Return conversations for a coach."""

    def list_by_athlete(self, athlete_id: UserId) -> list[Conversation]:
        """Return conversations for an athlete."""

    def touch_updated_at(
        self,
        conversation_id: ConversationId,
        *,
        updated_at: datetime,
    ) -> None:
        """Update conversation updated_at timestamp."""
