"""Unit tests for conversation use cases."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.security.coaching_access_guard import CoachingAccessGuard
from application.use_cases.conversation_commands import (
    MarkConversationReadUseCase,
    SendAthleteConversationMessageUseCase,
    SendCoachConversationMessageUseCase,
)
from application.use_cases.conversation_queries import ListConversationMessagesUseCase
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.conversation import Conversation
from domain.entities.conversation_message_kind import ConversationMessageKind
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, ConversationNotFoundError
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryCoachAthleteLinkRepository
from fakes.in_memory_conversation_repositories import (
    InMemoryConversationMessageRepository,
    InMemoryConversationRepository,
)


def _link_coach_and_athlete(
    link_repository: InMemoryCoachAthleteLinkRepository,
    coach_id: UserId,
    athlete_id: UserId,
) -> None:
    link_repository.save(
        CoachAthleteLink(
            id=CoachAthleteLinkId(uuid4()),
            coach_id=coach_id,
            athlete_id=athlete_id,
            created_at=datetime.now(UTC),
        )
    )


def test_coach_sends_message_creates_conversation() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    link_repository = InMemoryCoachAthleteLinkRepository()
    _link_coach_and_athlete(link_repository, coach_id, athlete_id)
    conversation_repository = InMemoryConversationRepository()
    message_repository = InMemoryConversationMessageRepository()
    use_case = SendCoachConversationMessageUseCase(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        access_guard=CoachingAccessGuard(link_repository),
    )

    view = use_case.execute(
        coach_id=coach_id,
        coach_role=Role.COACH,
        athlete_id=athlete_id,
        content="Привет!",
    )

    assert view.content == "Привет!"
    assert view.is_mine is True
    conversation = conversation_repository.get_by_coach_and_athlete(coach_id, athlete_id)
    assert conversation is not None
    assert message_repository.count_by_conversation(conversation.id) == 1


def test_athlete_sends_question_message() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    link_repository = InMemoryCoachAthleteLinkRepository()
    _link_coach_and_athlete(link_repository, coach_id, athlete_id)
    conversation_repository = InMemoryConversationRepository()
    message_repository = InMemoryConversationMessageRepository()
    use_case = SendAthleteConversationMessageUseCase(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        access_guard=CoachingAccessGuard(link_repository),
    )

    view = use_case.execute(
        athlete_id=athlete_id,
        athlete_role=Role.ATHLETE,
        coach_id=coach_id,
        content="Можно перенести тренировку?",
        kind=ConversationMessageKind.QUESTION,
    )

    assert view.kind == "question"
    assert view.is_mine is True


def test_list_messages_requires_participant() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    outsider_id = UserId(uuid4())
    link_repository = InMemoryCoachAthleteLinkRepository()
    _link_coach_and_athlete(link_repository, coach_id, athlete_id)
    conversation_repository = InMemoryConversationRepository()
    now = datetime.now(UTC)
    conversation_id = ConversationId(uuid4())
    conversation_repository.save(
        Conversation(
            id=conversation_id,
            coach_id=coach_id,
            athlete_id=athlete_id,
            created_at=now,
            updated_at=now,
        )
    )
    use_case = ListConversationMessagesUseCase(
        conversation_repository=conversation_repository,
        message_repository=InMemoryConversationMessageRepository(),
        access_guard=CoachingAccessGuard(link_repository),
    )

    with pytest.raises(ConversationNotFoundError):
        use_case.execute(
            actor_id=outsider_id,
            actor_role=Role.ATHLETE,
            conversation_id=conversation_id,
        )


def test_mark_read_marks_incoming_messages() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    link_repository = InMemoryCoachAthleteLinkRepository()
    _link_coach_and_athlete(link_repository, coach_id, athlete_id)
    conversation_repository = InMemoryConversationRepository()
    message_repository = InMemoryConversationMessageRepository()
    send_use_case = SendCoachConversationMessageUseCase(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        access_guard=CoachingAccessGuard(link_repository),
    )
    send_use_case.execute(
        coach_id=coach_id,
        coach_role=Role.COACH,
        athlete_id=athlete_id,
        content="План на завтра готов",
    )
    conversation = conversation_repository.get_by_coach_and_athlete(coach_id, athlete_id)
    assert conversation is not None

    marked_count = MarkConversationReadUseCase(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        access_guard=CoachingAccessGuard(link_repository),
    ).execute(
        actor_id=athlete_id,
        actor_role=Role.ATHLETE,
        conversation_id=conversation.id,
    )

    assert marked_count == 1
    assert message_repository.count_unread_for_recipient(conversation.id, athlete_id) == 0


def test_send_message_rejects_wrong_role() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    link_repository = InMemoryCoachAthleteLinkRepository()
    use_case = SendCoachConversationMessageUseCase(
        conversation_repository=InMemoryConversationRepository(),
        message_repository=InMemoryConversationMessageRepository(),
        access_guard=CoachingAccessGuard(link_repository),
    )

    with pytest.raises(AuthorizationError):
        use_case.execute(
            coach_id=athlete_id,
            coach_role=Role.ATHLETE,
            athlete_id=coach_id,
            content="test",
        )
