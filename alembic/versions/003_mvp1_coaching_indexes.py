"""Add composite indexes for MVP 1 coaching queries.

Revision ID: 003
Revises: 002
Create Date: 2026-06-29
"""

from collections.abc import Sequence

from alembic import op

revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composite indexes for coach and athlete queries."""
    op.create_index(
        "ix_invitations_coach_id_status",
        "invitations",
        ["coach_id", "status"],
    )
    op.create_index(
        "ix_personal_records_athlete_id_record_type",
        "personal_records",
        ["athlete_id", "record_type"],
    )
    op.create_index(
        "ix_workout_feedback_athlete_id_created_at",
        "workout_feedback",
        ["athlete_id", "created_at"],
    )


def downgrade() -> None:
    """Drop composite coaching indexes."""
    op.drop_index("ix_workout_feedback_athlete_id_created_at", table_name="workout_feedback")
    op.drop_index("ix_personal_records_athlete_id_record_type", table_name="personal_records")
    op.drop_index("ix_invitations_coach_id_status", table_name="invitations")
