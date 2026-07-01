"""Create MVP 1 coaching tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: str | Sequence[str] | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

invitation_status = postgresql.ENUM(
    "pending",
    "accepted",
    "declined",
    name="invitation_status",
    create_type=False,
)
athlete_gender = postgresql.ENUM(
    "male",
    "female",
    "other",
    "prefer_not_to_say",
    name="athlete_gender",
    create_type=False,
)
record_type = postgresql.ENUM(
    "distance",
    "exercise",
    name="record_type",
    create_type=False,
)


def upgrade() -> None:
    """Create coaching tables for MVP 1."""
    bind = op.get_bind()
    invitation_status.create(bind, checkfirst=True)
    athlete_gender.create(bind, checkfirst=True)
    record_type.create(bind, checkfirst=True)

    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("coach_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("athlete_email", sa.String(length=320), nullable=False),
        sa.Column("status", invitation_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_invitations_coach_id", "invitations", ["coach_id"])
    op.create_index("ix_invitations_athlete_email", "invitations", ["athlete_email"])
    op.create_index("ix_invitations_status", "invitations", ["status"])

    op.create_table(
        "coach_athlete_links",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("coach_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("coach_id", "athlete_id", name="uq_coach_athlete_links_pair"),
    )
    op.create_index("ix_coach_athlete_links_coach_id", "coach_athlete_links", ["coach_id"])
    op.create_index("ix_coach_athlete_links_athlete_id", "coach_athlete_links", ["athlete_id"])

    op.create_table(
        "athlete_profiles",
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("height_cm", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Integer(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", athlete_gender, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "personal_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("record_type", record_type, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("value", sa.String(length=64), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("achieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_personal_records_athlete_id", "personal_records", ["athlete_id"])

    op.create_table(
        "workout_feedback",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("garmin_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_workout_feedback_athlete_id", "workout_feedback", ["athlete_id"])


def downgrade() -> None:
    """Drop coaching tables."""
    op.drop_index("ix_workout_feedback_athlete_id", table_name="workout_feedback")
    op.drop_table("workout_feedback")
    op.drop_index("ix_personal_records_athlete_id", table_name="personal_records")
    op.drop_table("personal_records")
    op.drop_table("athlete_profiles")
    op.drop_index("ix_coach_athlete_links_athlete_id", table_name="coach_athlete_links")
    op.drop_index("ix_coach_athlete_links_coach_id", table_name="coach_athlete_links")
    op.drop_table("coach_athlete_links")
    op.drop_index("ix_invitations_status", table_name="invitations")
    op.drop_index("ix_invitations_athlete_email", table_name="invitations")
    op.drop_index("ix_invitations_coach_id", table_name="invitations")
    op.drop_table("invitations")
    record_type.drop(op.get_bind(), checkfirst=True)
    athlete_gender.drop(op.get_bind(), checkfirst=True)
    invitation_status.drop(op.get_bind(), checkfirst=True)
