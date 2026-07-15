"""Add MVP 2.2 agent session tables.

Revision ID: 006
Revises: 005
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

agent_session_kind = postgresql.ENUM(
    "plan_creation",
    "report_assistance",
    name="agent_session_kind",
    create_type=False,
)
agent_session_status = postgresql.ENUM(
    "active",
    "completed",
    "abandoned",
    name="agent_session_status",
    create_type=False,
)
agent_message_role = postgresql.ENUM(
    "user",
    "assistant",
    "system",
    name="agent_message_role",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    agent_session_kind.create(bind, checkfirst=True)
    agent_session_status.create(bind, checkfirst=True)
    agent_message_role.create(bind, checkfirst=True)

    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", agent_session_kind, nullable=False),
        sa.Column(
            "coach_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "athlete_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "planned_workout_id",
            sa.Uuid(),
            sa.ForeignKey("planned_workouts.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("status", agent_session_status, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_sessions_coach_id", "agent_sessions", ["coach_id"])
    op.create_index("ix_agent_sessions_athlete_id", "agent_sessions", ["athlete_id"])
    op.create_index(
        "ix_agent_sessions_planned_workout_id",
        "agent_sessions",
        ["planned_workout_id"],
    )
    op.create_index("ix_agent_sessions_status", "agent_sessions", ["status"])

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", agent_message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_messages_session_id", "agent_messages", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_messages_session_id", table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_index("ix_agent_sessions_status", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_planned_workout_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_athlete_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_coach_id", table_name="agent_sessions")
    op.drop_table("agent_sessions")

    bind = op.get_bind()
    agent_message_role.drop(bind, checkfirst=True)
    agent_session_status.drop(bind, checkfirst=True)
    agent_session_kind.drop(bind, checkfirst=True)
