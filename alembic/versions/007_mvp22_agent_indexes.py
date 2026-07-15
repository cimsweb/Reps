"""Add MVP 2.2 agent session indexes and invariants.

Revision ID: 007
Revises: 006
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | Sequence[str] | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_agent_sessions_coach_id_status",
        "agent_sessions",
        ["coach_id", "status"],
    )
    op.create_index(
        "ix_agent_sessions_athlete_id_status",
        "agent_sessions",
        ["athlete_id", "status"],
    )
    op.create_index(
        "uq_agent_sessions_active_report_per_workout",
        "agent_sessions",
        ["planned_workout_id"],
        unique=True,
        postgresql_where=sa.text(
            "status = 'active' AND kind = 'report_assistance' AND planned_workout_id IS NOT NULL"
        ),
    )
    op.create_index(
        "ix_agent_messages_session_id_sort_order",
        "agent_messages",
        ["session_id", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_messages_session_id_sort_order", table_name="agent_messages")
    op.drop_index("uq_agent_sessions_active_report_per_workout", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_athlete_id_status", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_coach_id_status", table_name="agent_sessions")
