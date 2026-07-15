"""Conversation read use cases."""

from application.dto.conversation import (
    ConversationMessageView,
    ConversationSummaryView,
    PaginatedConversationMessages,
)
from application.security.coaching_access_guard import CoachingAccessGuard
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, ConversationNotFoundError
from domain.repositories.conversation_message_repository import ConversationMessageRepository
from domain.repositories.conversation_repository import ConversationRepository
from domain.repositories.user_repository import UserRepository
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.pagination import PageRequest
from domain.value_objects.user_id import UserId


class ListCoachConversationsUseCase:
    """Return conversations for a coach."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: ConversationMessageRepository,
        user_repository: UserRepository,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._user_repository = user_repository

    def execute(self, coach_id: UserId, coach_role: Role) -> list[ConversationSummaryView]:
        if coach_role is not Role.COACH:
            raise AuthorizationError("Only coaches can list conversations")

        conversations = self._conversation_repository.list_by_coach(coach_id)
        return [self._to_summary(conversation, coach_id) for conversation in conversations]

    def _to_summary(self, conversation, actor_id: UserId) -> ConversationSummaryView:
        partner_id = conversation.athlete_id
        partner = self._user_repository.get_by_id(partner_id)
        partner_email = str(partner.email) if partner else ""
        last_message = self._message_repository.get_latest_by_conversation(conversation.id)
        unread_count = self._message_repository.count_unread_for_recipient(
            conversation.id,
            actor_id,
        )
        return ConversationSummaryView.from_conversation(
            conversation,
            partner_id=str(partner_id.value),
            partner_email=partner_email,
            unread_count=unread_count,
            last_message=last_message,
        )


class ListAthleteConversationsUseCase:
    """Return conversations for an athlete."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: ConversationMessageRepository,
        user_repository: UserRepository,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._user_repository = user_repository

    def execute(self, athlete_id: UserId, athlete_role: Role) -> list[ConversationSummaryView]:
        if athlete_role is not Role.ATHLETE:
            raise AuthorizationError("Only athletes can list conversations")

        conversations = self._conversation_repository.list_by_athlete(athlete_id)
        return [self._to_summary(conversation, athlete_id) for conversation in conversations]

    def _to_summary(self, conversation, actor_id: UserId) -> ConversationSummaryView:
        partner_id = conversation.coach_id
        partner = self._user_repository.get_by_id(partner_id)
        partner_email = str(partner.email) if partner else ""
        last_message = self._message_repository.get_latest_by_conversation(conversation.id)
        unread_count = self._message_repository.count_unread_for_recipient(
            conversation.id,
            actor_id,
        )
        return ConversationSummaryView.from_conversation(
            conversation,
            partner_id=str(partner_id.value),
            partner_email=partner_email,
            unread_count=unread_count,
            last_message=last_message,
        )


class ListConversationMessagesUseCase:
    """Return paginated messages for a conversation."""

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
        page: PageRequest | None = None,
    ) -> PaginatedConversationMessages:
        conversation = self._require_conversation(conversation_id)
        self._ensure_access(actor_id, actor_role, conversation)

        page_request = page or PageRequest()
        messages = self._message_repository.list_by_conversation(
            conversation_id,
            offset=page_request.offset,
            limit=page_request.limit,
        )
        total = self._message_repository.count_by_conversation(conversation_id)
        actor_id_str = str(actor_id.value)
        return PaginatedConversationMessages(
            items=tuple(
                ConversationMessageView.from_message(message, actor_id=actor_id_str)
                for message in messages
            ),
            total=total,
        )

    def _require_conversation(self, conversation_id: ConversationId):
        conversation = self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return conversation

    def _ensure_access(self, actor_id: UserId, actor_role: Role, conversation) -> None:
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
        raise AuthorizationError("Only coaches and athletes can view conversations")
