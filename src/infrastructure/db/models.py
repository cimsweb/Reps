import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from domain.entities.agent_message_role import AgentMessageRole
from domain.entities.agent_session_kind import AgentSessionKind
from domain.entities.agent_session_status import AgentSessionStatus
from domain.entities.conversation_message_kind import ConversationMessageKind
from domain.entities.gender import Gender
from domain.entities.invitation_status import InvitationStatus
from domain.entities.plan_scope import PlanScope
from domain.entities.record_type import RecordType
from domain.entities.role import Role
from domain.entities.workout_type import WorkoutType


def _enum_values(enum_type: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_type]


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class UserRecord(Base):
    """Users table mapping."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", values_callable=_enum_values),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sessions: Mapped[list["SessionRecord"]] = relationship(back_populates="user")


class SessionRecord(Base):
    """Sessions table mapping."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[UserRecord] = relationship(back_populates="sessions")


class InvitationRecord(Base):
    """Invitations table mapping."""

    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus, name="invitation_status", values_callable=_enum_values),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CoachAthleteLinkRecord(Base):
    """Coach-athlete links table mapping."""

    __tablename__ = "coach_athlete_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AthleteProfileRecord(Base):
    """Athlete profiles table mapping."""

    __tablename__ = "athlete_profiles"

    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    height_cm: Mapped[int] = mapped_column(nullable=False)
    weight_kg: Mapped[int] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="athlete_gender", values_callable=_enum_values),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PersonalRecordRecord(Base):
    """Personal records table mapping."""

    __tablename__ = "personal_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_type: Mapped[RecordType] = mapped_column(
        Enum(RecordType, name="record_type", values_callable=_enum_values),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkoutFeedbackRecord(Base):
    """Workout feedback table mapping."""

    __tablename__ = "workout_feedback"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TrainingPlanRecord(Base):
    """Training plans table mapping."""

    __tablename__ = "training_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope: Mapped[PlanScope] = mapped_column(
        Enum(PlanScope, name="plan_scope", values_callable=_enum_values),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    workouts: Mapped[list["PlannedWorkoutRecord"]] = relationship(back_populates="plan")


class PlannedWorkoutRecord(Base):
    """Planned workouts table mapping."""

    __tablename__ = "planned_workouts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coach_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    planned_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    workout_type: Mapped[WorkoutType] = mapped_column(
        Enum(WorkoutType, name="workout_type", values_callable=_enum_values),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    plan: Mapped[TrainingPlanRecord] = relationship(back_populates="workouts")
    cycles: Mapped[list["WorkoutCycleRecord"]] = relationship(back_populates="workout")
    completion_report: Mapped["WorkoutCompletionReportRecord | None"] = relationship(
        back_populates="planned_workout",
        uselist=False,
    )


class WorkoutCycleRecord(Base):
    """Workout cycles table mapping."""

    __tablename__ = "workout_cycles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    planned_workout_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("planned_workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    workout: Mapped[PlannedWorkoutRecord] = relationship(back_populates="cycles")
    exercises: Mapped[list["WorkoutExerciseRecord"]] = relationship(back_populates="cycle")


class WorkoutExerciseRecord(Base):
    """Workout exercises table mapping."""

    __tablename__ = "workout_exercises"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workout_cycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    cycle: Mapped[WorkoutCycleRecord] = relationship(back_populates="exercises")


class WorkoutCompletionReportRecord(Base):
    """Workout completion reports table mapping."""

    __tablename__ = "workout_completion_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    planned_workout_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("planned_workouts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    difficulty_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    mood_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    garmin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_report_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    planned_workout: Mapped[PlannedWorkoutRecord] = relationship(back_populates="completion_report")


class AgentSessionRecord(Base):
    """Agent dialog sessions table mapping."""

    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    kind: Mapped[AgentSessionKind] = mapped_column(
        Enum(AgentSessionKind, name="agent_session_kind", values_callable=_enum_values),
        nullable=False,
    )
    coach_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    planned_workout_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("planned_workouts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    status: Mapped[AgentSessionStatus] = mapped_column(
        Enum(AgentSessionStatus, name="agent_session_status", values_callable=_enum_values),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    messages: Mapped[list["AgentMessageRecord"]] = relationship(back_populates="session")


class AgentMessageRecord(Base):
    """Agent dialog messages table mapping."""

    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[AgentMessageRole] = mapped_column(
        Enum(AgentMessageRole, name="agent_message_role", values_callable=_enum_values),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict[str, object] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[AgentSessionRecord] = relationship(back_populates="messages")


class ConversationRecord(Base):
    """Coach-athlete conversations table mapping."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    messages: Mapped[list["ConversationMessageRecord"]] = relationship(
        back_populates="conversation",
    )


class ConversationMessageRecord(Base):
    """Conversation messages table mapping."""

    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[ConversationMessageKind] = mapped_column(
        Enum(
            ConversationMessageKind,
            name="conversation_message_kind",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    conversation: Mapped[ConversationRecord] = relationship(back_populates="messages")
