"""Remove Garmin API integration tables and coaching feedback garmin_url.

Revision ID: 011
Revises: 010
Create Date: 2026-07-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: str | Sequence[str] | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_sync_jobs_athlete_id_created_at", table_name="sync_jobs")
    op.drop_table("sync_jobs")

    op.drop_index("ix_imported_activities_garmin_connection_id", table_name="imported_activities")
    op.drop_index(
        "ix_imported_activities_athlete_id_activity_type",
        table_name="imported_activities",
    )
    op.drop_index(
        "ix_imported_activities_athlete_id_activity_date",
        table_name="imported_activities",
    )
    op.drop_index("uq_imported_activities_garmin_activity_id", table_name="imported_activities")
    op.drop_index(
        "ix_imported_activities_athlete_id_started_at",
        table_name="imported_activities",
    )
    op.drop_table("imported_activities")

    op.drop_index("ix_garmin_connections_athlete_id_status", table_name="garmin_connections")
    op.drop_table("garmin_connections")

    bind = op.get_bind()
    postgresql.ENUM(name="sync_job_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="garmin_connection_status").drop(bind, checkfirst=True)

    op.drop_column("workout_feedback", "garmin_url")


def downgrade() -> None:
    op.add_column(
        "workout_feedback",
        sa.Column("garmin_url", sa.String(length=2048), nullable=True),
    )

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
        sa.Column("garmin_connection_id", sa.Uuid(), nullable=False),
        sa.Column("garmin_activity_id", sa.String(length=128), nullable=False),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("distance_meters", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("average_heart_rate", sa.Integer(), nullable=True),
        sa.Column("elevation_gain_meters", sa.Integer(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["garmin_connection_id"],
            ["garmin_connections.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_imported_activities_athlete_id_started_at",
        "imported_activities",
        ["athlete_id", "started_at"],
    )
    op.create_index(
        "uq_imported_activities_garmin_activity_id",
        "imported_activities",
        ["garmin_activity_id"],
        unique=True,
    )
    op.create_index(
        "ix_imported_activities_athlete_id_activity_date",
        "imported_activities",
        ["athlete_id", "activity_date"],
    )
    op.create_index(
        "ix_imported_activities_athlete_id_activity_type",
        "imported_activities",
        ["athlete_id", "activity_type"],
    )
    op.create_index(
        "ix_imported_activities_garmin_connection_id",
        "imported_activities",
        ["garmin_connection_id"],
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
