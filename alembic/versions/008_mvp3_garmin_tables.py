"""Add MVP 3 Garmin integration tables.

Revision ID: 008
Revises: 007
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: str | Sequence[str] | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

garmin_connection_status = postgresql.ENUM(
    "connected",
    "disconnected",
    "reconnect_required",
    name="garmin_connection_status",
    create_type=False,
)
sync_job_status = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    name="sync_job_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    garmin_connection_status.create(bind, checkfirst=True)
    sync_job_status.create(bind, checkfirst=True)

    op.create_table(
        "garmin_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("status", garmin_connection_status, nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("athlete_id", name="uq_garmin_connections_athlete_id"),
    )
    op.create_index(
        "ix_garmin_connections_athlete_id_status",
        "garmin_connections",
        ["athlete_id", "status"],
    )

    op.create_table(
        "imported_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("garmin_activity_id", sa.String(length=128), nullable=False),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("distance_meters", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("average_heart_rate", sa.Integer(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "athlete_id",
            "garmin_activity_id",
            name="uq_imported_activities_athlete_garmin_id",
        ),
    )
    op.create_index(
        "ix_imported_activities_athlete_id_started_at",
        "imported_activities",
        ["athlete_id", "started_at"],
    )

    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.Uuid(), nullable=False),
        sa.Column("status", sync_job_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_jobs_athlete_id_created_at", "sync_jobs", ["athlete_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_sync_jobs_athlete_id_created_at", table_name="sync_jobs")
    op.drop_table("sync_jobs")
    op.drop_index("ix_imported_activities_athlete_id_started_at", table_name="imported_activities")
    op.drop_table("imported_activities")
    op.drop_index("ix_garmin_connections_athlete_id_status", table_name="garmin_connections")
    op.drop_table("garmin_connections")
    bind = op.get_bind()
    sync_job_status.drop(bind, checkfirst=True)
    garmin_connection_status.drop(bind, checkfirst=True)
