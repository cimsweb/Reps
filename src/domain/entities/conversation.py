from dataclasses import dataclass
from datetime import datetime

from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class Conversation:
    """Coach-athlete messaging thread."""

    id: ConversationId
    coach_id: UserId
    athlete_id: UserId
    created_at: datetime
    updated_at: datetime
