from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from domain.entities.conversation import Conversation
from domain.entities.conversation_message import ConversationMessage
from domain.exceptions import ConversationNotFoundError
from domain.value_objects.conversation_id import ConversationId
from domain.value_objects.conversation_message_id import ConversationMessageId
from domain.value_objects.user_id import UserId
from infrastructure.db.models import ConversationMessageRecord, ConversationRecord


def _to_domain_conversation(record: ConversationRecord) -> Conversation:
    return Conversation(
        id=ConversationId(record.id),
        coach_id=UserId(record.coach_id),
        athlete_id=UserId(record.athlete_id),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _to_domain_message(record: ConversationMessageRecord) -> ConversationMessage:
    return ConversationMessage(
        id=ConversationMessageId(record.id),
        conversation_id=ConversationId(record.conversation_id),
        sender_id=UserId(record.sender_id),
        kind=record.kind,
        content=record.content,
        sort_order=record.sort_order,
        read_at=record.read_at,
        created_at=record.created_at,
    )


class SqlAlchemyConversationRepository:
    """SQLAlchemy implementation of ConversationRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, conversation: Conversation) -> Conversation:
        record = self._db_session.get(ConversationRecord, conversation.id.value)
        if record is None:
            record = ConversationRecord(
                id=conversation.id.value,
                coach_id=conversation.coach_id.value,
                athlete_id=conversation.athlete_id.value,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
            self._db_session.add(record)
        else:
            record.coach_id = conversation.coach_id.value
            record.athlete_id = conversation.athlete_id.value
            record.created_at = conversation.created_at
            record.updated_at = conversation.updated_at

        self._db_session.flush()
        return _to_domain_conversation(record)

    def get_by_id(self, conversation_id: ConversationId) -> Conversation | None:
        record = self._db_session.get(ConversationRecord, conversation_id.value)
        return _to_domain_conversation(record) if record else None

    def get_by_coach_and_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> Conversation | None:
        stmt = select(ConversationRecord).where(
            ConversationRecord.coach_id == coach_id.value,
            ConversationRecord.athlete_id == athlete_id.value,
        )
        record = self._db_session.scalars(stmt).first()
        return _to_domain_conversation(record) if record else None

    def list_by_coach(self, coach_id: UserId) -> list[Conversation]:
        stmt = (
            select(ConversationRecord)
            .where(ConversationRecord.coach_id == coach_id.value)
            .order_by(ConversationRecord.updated_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_conversation(record) for record in records]

    def list_by_athlete(self, athlete_id: UserId) -> list[Conversation]:
        stmt = (
            select(ConversationRecord)
            .where(ConversationRecord.athlete_id == athlete_id.value)
            .order_by(ConversationRecord.updated_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_conversation(record) for record in records]

    def touch_updated_at(
        self,
        conversation_id: ConversationId,
        *,
        updated_at: datetime,
    ) -> None:
        record = self._db_session.get(ConversationRecord, conversation_id.value)
        if record is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        record.updated_at = updated_at
        self._db_session.flush()


class SqlAlchemyConversationMessageRepository:
    """SQLAlchemy implementation of ConversationMessageRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def append(self, message: ConversationMessage) -> ConversationMessage:
        record = ConversationMessageRecord(
            id=message.id.value,
            conversation_id=message.conversation_id.value,
            sender_id=message.sender_id.value,
            kind=message.kind,
            content=message.content,
            sort_order=message.sort_order,
            read_at=message.read_at,
            created_at=message.created_at,
        )
        self._db_session.add(record)
        self._db_session.flush()
        return _to_domain_message(record)

    def list_by_conversation(
        self,
        conversation_id: ConversationId,
        *,
        offset: int,
        limit: int,
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessageRecord)
            .where(ConversationMessageRecord.conversation_id == conversation_id.value)
            .order_by(ConversationMessageRecord.sort_order.asc())
            .offset(offset)
            .limit(limit)
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_message(record) for record in records]

    def count_by_conversation(self, conversation_id: ConversationId) -> int:
        stmt = (
            select(func.count())
            .select_from(ConversationMessageRecord)
            .where(ConversationMessageRecord.conversation_id == conversation_id.value)
        )
        return int(self._db_session.scalar(stmt) or 0)

    def get_latest_by_conversation(
        self,
        conversation_id: ConversationId,
    ) -> ConversationMessage | None:
        stmt = (
            select(ConversationMessageRecord)
            .where(ConversationMessageRecord.conversation_id == conversation_id.value)
            .order_by(ConversationMessageRecord.sort_order.desc())
            .limit(1)
        )
        record = self._db_session.scalars(stmt).first()
        return _to_domain_message(record) if record else None

    def count_unread_for_recipient(
        self,
        conversation_id: ConversationId,
        recipient_id: UserId,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ConversationMessageRecord)
            .where(
                ConversationMessageRecord.conversation_id == conversation_id.value,
                ConversationMessageRecord.sender_id != recipient_id.value,
                ConversationMessageRecord.read_at.is_(None),
            )
        )
        return int(self._db_session.scalar(stmt) or 0)

    def mark_read_for_recipient(
        self,
        conversation_id: ConversationId,
        recipient_id: UserId,
        *,
        read_at: datetime,
    ) -> int:
        stmt = (
            update(ConversationMessageRecord)
            .where(
                ConversationMessageRecord.conversation_id == conversation_id.value,
                ConversationMessageRecord.sender_id != recipient_id.value,
                ConversationMessageRecord.read_at.is_(None),
            )
            .values(read_at=read_at)
        )
        result = self._db_session.execute(stmt)
        self._db_session.flush()
        return int(getattr(result, "rowcount", 0) or 0)

    def next_sort_order(self, conversation_id: ConversationId) -> int:
        stmt = select(func.coalesce(func.max(ConversationMessageRecord.sort_order), -1)).where(
            ConversationMessageRecord.conversation_id == conversation_id.value
        )
        current_max = self._db_session.scalar(stmt)
        return int(current_max or -1) + 1
