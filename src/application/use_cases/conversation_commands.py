"""Conversation write use cases."""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from application.dto.conversation import ConversationMessageView
from application.security.coaching_access_guard import CoachingAccessGuard
from domain.entities.conversation import Conversation
from domain.entities.conversation_message import ConversationMessage
from domain.entities.conversation_message_kind import ConversationMessageKind
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, ConversationNotFoundError
from domain.repositories.conversation_message_repository import ConversationMessageRepository
from domain.repositories.conversation_repository import ConversationRepository
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.conversation_message_content import ConversationMessageContent
from domain.value_objects.conversation_message_id import ConversationMessageId
from domain.value_objects.user_id import UserId


class SendCoachConversationMessageUseCase:
    """Coach sends a message to a linked athlete."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: ConversationMessageRepository,
        access_guard: CoachingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.conversations")

    def execute(
        self,
        *,
        coach_id: UserId,
        coach_role: Role,
        athlete_id: UserId,
        content: str,
        kind: ConversationMessageKind = ConversationMessageKind.TEXT,
    ) -> ConversationMessageView:
        if coach_role is not Role.COACH:
            raise AuthorizationError("Only coaches can send coach messages")

        self._access_guard.ensure_coach_can_access_athlete(coach_id, athlete_id)
        validated_content = ConversationMessageContent(content)
        conversation = self._get_or_create_conversation(coach_id, athlete_id)
        message = self._append_message(
            conversation_id=conversation.id,
            sender_id=coach_id,
            content=validated_content.value,
            kind=kind,
        )
        self._logger.info(
            "conversation_message_sent coach_id=%s athlete_id=%s conversation_id=%s",
            coach_id,
            athlete_id,
            conversation.id,
        )
        return ConversationMessageView.from_message(
            message,
            actor_id=str(coach_id.value),
        )

    def _get_or_create_conversation(self, coach_id: UserId, athlete_id: UserId) -> Conversation:
        existing = self._conversation_repository.get_by_coach_and_athlete(coach_id, athlete_id)
        if existing is not None:
            return existing

        now = datetime.now(UTC)
        return self._conversation_repository.save(
            Conversation(
                id=ConversationId(uuid4()),
                coach_id=coach_id,
                athlete_id=athlete_id,
                created_at=now,
                updated_at=now,
            )
        )

    def _append_message(
        self,
        *,
        conversation_id: ConversationId,
        sender_id: UserId,
        content: str,
        kind: ConversationMessageKind,
    ) -> ConversationMessage:
        return _append_message(
            self._conversation_repository,
            self._message_repository,
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            kind=kind,
        )


class SendAthleteConversationMessageUseCase:
    """Athlete sends a message to a linked coach."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: ConversationMessageRepository,
        access_guard: CoachingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.conversations")

    def execute(
        self,
        *,
        athlete_id: UserId,
        athlete_role: Role,
        coach_id: UserId,
        content: str,
        kind: ConversationMessageKind = ConversationMessageKind.TEXT,
    ) -> ConversationMessageView:
        if athlete_role is not Role.ATHLETE:
            raise AuthorizationError("Only athletes can send athlete messages")

        self._access_guard.ensure_coach_can_access_athlete(coach_id, athlete_id)
        self._access_guard.ensure_athlete_owns_data(athlete_id, athlete_id)
        validated_content = ConversationMessageContent(content)
        conversation = self._get_or_create_conversation(coach_id, athlete_id)
        message = self._append_message(
            conversation_id=conversation.id,
            sender_id=athlete_id,
            content=validated_content.value,
            kind=kind,
        )
        self._logger.info(
            "conversation_message_sent athlete_id=%s coach_id=%s conversation_id=%s",
            athlete_id,
            coach_id,
            conversation.id,
        )
        return ConversationMessageView.from_message(
            message,
            actor_id=str(athlete_id.value),
        )

    def _get_or_create_conversation(self, coach_id: UserId, athlete_id: UserId) -> Conversation:
        existing = self._conversation_repository.get_by_coach_and_athlete(coach_id, athlete_id)
        if existing is not None:
            return existing

        now = datetime.now(UTC)
        return self._conversation_repository.save(
            Conversation(
                id=ConversationId(uuid4()),
                coach_id=coach_id,
                athlete_id=athlete_id,
                created_at=now,
                updated_at=now,
            )
        )

    def _append_message(
        self,
        *,
        conversation_id: ConversationId,
        sender_id: UserId,
        content: str,
        kind: ConversationMessageKind,
    ) -> ConversationMessage:
        return _append_message(
            self._conversation_repository,
            self._message_repository,
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            kind=kind,
        )


class MarkConversationReadUseCase:
    """Mark incoming messages as read for the current user."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: ConversationMessageRepository,
        access_guard: CoachingAccessGuard,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._access_guard = access_guard

    def execute(
        self,
        *,
        actor_id: UserId,
        actor_role: Role,
        conversation_id: ConversationId,
    ) -> int:
        conversation = self._require_conversation(conversation_id)
        self._ensure_access(actor_id, actor_role, conversation)
        return self._message_repository.mark_read_for_recipient(
            conversation_id,
            actor_id,
            read_at=datetime.now(UTC),
        )

    def _require_conversation(self, conversation_id: ConversationId) -> Conversation:
        conversation = self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return conversation

    def _ensure_access(
        self,
        actor_id: UserId,
        actor_role: Role,
        conversation: Conversation,
    ) -> None:
        if actor_role is Role.COACH:
            if conversation.coach_id != actor_id:
                raise ConversationNotFoundError(f"Conversation not found: {conversation.id}")
            self._access_guard.ensure_coach_can_access_athlete(
                actor_id,
                conversation.athlete_id,
            )
            return
        if actor_role is Role.ATHLETE:
            if conversation.athlete_id != actor_id:
                raise ConversationNotFoundError(f"Conversation not found: {conversation.id}")
            self._access_guard.ensure_athlete_owns_data(actor_id, conversation.athlete_id)
            return
        raise AuthorizationError("Only coaches and athletes can mark conversations read")


def _append_message(
    conversation_repository: ConversationRepository,
    message_repository: ConversationMessageRepository,
    *,
    conversation_id: ConversationId,
    sender_id: UserId,
    content: str,
    kind: ConversationMessageKind,
) -> ConversationMessage:
    now = datetime.now(UTC)
    sort_order = message_repository.next_sort_order(conversation_id)
    conversation_repository.touch_updated_at(conversation_id, updated_at=now)

    return message_repository.append(
        ConversationMessage(
            id=ConversationMessageId(uuid4()),
            conversation_id=conversation_id,
            sender_id=sender_id,
            kind=kind,
            content=content,
            sort_order=sort_order,
            read_at=None,
            created_at=now,
        )
    )
