from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.entities.agent_message import AgentMessage
from domain.entities.agent_session import AgentSession
from domain.entities.agent_session_kind import AgentSessionKind
from domain.entities.agent_session_status import AgentSessionStatus
from domain.exceptions import (
    AgentSessionNotFoundError,
    DuplicateActiveReportAgentSessionError,
)
from domain.services.agent_session_rules import AGENT_SESSION_EXPIRY_HOURS
from domain.value_objects.agent_message_id import AgentMessageId
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId
from infrastructure.db.models import AgentMessageRecord, AgentSessionRecord


def _to_domain_session(record: AgentSessionRecord) -> AgentSession:
    return AgentSession(
        id=AgentSessionId(record.id),
        kind=record.kind,
        coach_id=UserId(record.coach_id) if record.coach_id else None,
        athlete_id=UserId(record.athlete_id),
        planned_workout_id=(
            PlannedWorkoutId(record.planned_workout_id) if record.planned_workout_id else None
        ),
        status=record.status,
        start_date=record.start_date,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _to_domain_message(record: AgentMessageRecord) -> AgentMessage:
    return AgentMessage(
        id=AgentMessageId(record.id),
        session_id=AgentSessionId(record.session_id),
        role=record.role,
        content=record.content,
        metadata=record.message_metadata,
        sort_order=record.sort_order,
        created_at=record.created_at,
    )


class SqlAlchemyAgentSessionRepository:
    """SQLAlchemy implementation of AgentSessionRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, session: AgentSession) -> AgentSession:
        record = self._db_session.get(AgentSessionRecord, session.id.value)
        coach_id = session.coach_id.value if session.coach_id else None
        planned_workout_id = (
            session.planned_workout_id.value if session.planned_workout_id else None
        )
        if record is None:
            record = AgentSessionRecord(
                id=session.id.value,
                kind=session.kind,
                coach_id=coach_id,
                athlete_id=session.athlete_id.value,
                planned_workout_id=planned_workout_id,
                status=session.status,
                start_date=session.start_date,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
            self._db_session.add(record)
        else:
            record.kind = session.kind
            record.coach_id = coach_id
            record.athlete_id = session.athlete_id.value
            record.planned_workout_id = planned_workout_id
            record.status = session.status
            record.start_date = session.start_date
            record.created_at = session.created_at
            record.updated_at = session.updated_at

        try:
            self._db_session.flush()
        except IntegrityError as error:
            if "uq_agent_sessions_active_report_per_workout" in str(error.orig):
                raise DuplicateActiveReportAgentSessionError(
                    "Active report agent session already exists for this workout"
                ) from error
            raise
        return _to_domain_session(record)

    def get_by_id(self, session_id: AgentSessionId) -> AgentSession | None:
        record = self._db_session.get(AgentSessionRecord, session_id.value)
        return _to_domain_session(record) if record else None

    def get_active_report_session(
        self,
        planned_workout_id: PlannedWorkoutId,
    ) -> AgentSession | None:
        stmt = (
            select(AgentSessionRecord)
            .where(
                AgentSessionRecord.planned_workout_id == planned_workout_id.value,
                AgentSessionRecord.kind == AgentSessionKind.REPORT_ASSISTANCE,
                AgentSessionRecord.status == AgentSessionStatus.ACTIVE,
            )
            .limit(1)
        )
        record = self._db_session.scalars(stmt).first()
        return _to_domain_session(record) if record else None

    def list_active_by_coach(self, coach_id: UserId) -> list[AgentSession]:
        stmt = (
            select(AgentSessionRecord)
            .where(
                AgentSessionRecord.coach_id == coach_id.value,
                AgentSessionRecord.status == AgentSessionStatus.ACTIVE,
                AgentSessionRecord.kind == AgentSessionKind.PLAN_CREATION,
            )
            .order_by(AgentSessionRecord.updated_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_session(record) for record in records]

    def list_active_by_athlete(self, athlete_id: UserId) -> list[AgentSession]:
        stmt = (
            select(AgentSessionRecord)
            .where(
                AgentSessionRecord.athlete_id == athlete_id.value,
                AgentSessionRecord.status == AgentSessionStatus.ACTIVE,
            )
            .order_by(AgentSessionRecord.updated_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_session(record) for record in records]

    def get_active_plan_session_for_coach_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> AgentSession | None:
        stmt = (
            select(AgentSessionRecord)
            .where(
                AgentSessionRecord.coach_id == coach_id.value,
                AgentSessionRecord.athlete_id == athlete_id.value,
                AgentSessionRecord.status == AgentSessionStatus.ACTIVE,
                AgentSessionRecord.kind == AgentSessionKind.PLAN_CREATION,
            )
            .order_by(AgentSessionRecord.updated_at.desc())
            .limit(1)
        )
        record = self._db_session.scalars(stmt).first()
        return _to_domain_session(record) if record else None

    def complete(self, session_id: AgentSessionId, *, now: datetime | None = None) -> AgentSession:
        session = self._require_session(session_id)
        current_time = now or datetime.now(UTC)
        completed = AgentSession(
            id=session.id,
            kind=session.kind,
            coach_id=session.coach_id,
            athlete_id=session.athlete_id,
            planned_workout_id=session.planned_workout_id,
            status=AgentSessionStatus.COMPLETED,
            start_date=session.start_date,
            created_at=session.created_at,
            updated_at=current_time,
        )
        return self.save(completed)

    def abandon(self, session_id: AgentSessionId, *, now: datetime | None = None) -> AgentSession:
        session = self._require_session(session_id)
        current_time = now or datetime.now(UTC)
        abandoned = AgentSession(
            id=session.id,
            kind=session.kind,
            coach_id=session.coach_id,
            athlete_id=session.athlete_id,
            planned_workout_id=session.planned_workout_id,
            status=AgentSessionStatus.ABANDONED,
            start_date=session.start_date,
            created_at=session.created_at,
            updated_at=current_time,
        )
        return self.save(abandoned)

    def abandon_expired_active_sessions(self, *, now: datetime | None = None) -> int:
        current_time = now or datetime.now(UTC)
        expiry_threshold = current_time - timedelta(hours=AGENT_SESSION_EXPIRY_HOURS)
        expired_sessions = self._db_session.scalars(
            select(AgentSessionRecord.id).where(
                AgentSessionRecord.status == AgentSessionStatus.ACTIVE,
                AgentSessionRecord.updated_at < expiry_threshold,
            )
        ).all()
        if not expired_sessions:
            return 0
        stmt = (
            update(AgentSessionRecord)
            .where(AgentSessionRecord.id.in_(expired_sessions))
            .values(
                status=AgentSessionStatus.ABANDONED,
                updated_at=current_time,
            )
        )
        self._db_session.execute(stmt)
        self._db_session.flush()
        return len(expired_sessions)

    def _require_session(self, session_id: AgentSessionId) -> AgentSession:
        session = self.get_by_id(session_id)
        if session is None:
            raise AgentSessionNotFoundError(f"Agent session not found: {session_id}")
        return session


class SqlAlchemyAgentMessageRepository:
    """SQLAlchemy implementation of AgentMessageRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def append(self, message: AgentMessage) -> AgentMessage:
        record = AgentMessageRecord(
            id=message.id.value,
            session_id=message.session_id.value,
            role=message.role,
            content=message.content,
            message_metadata=message.metadata,
            sort_order=message.sort_order,
            created_at=message.created_at,
        )
        self._db_session.add(record)
        self._db_session.flush()
        return _to_domain_message(record)

    def list_by_session(self, session_id: AgentSessionId) -> list[AgentMessage]:
        stmt = (
            select(AgentMessageRecord)
            .where(AgentMessageRecord.session_id == session_id.value)
            .order_by(AgentMessageRecord.sort_order.asc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_message(record) for record in records]
