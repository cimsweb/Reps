"""Add MVP 3 Garmin activity indexing columns and indexes.

Revision ID: 009
Revises: 008
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "imported_activities",
        sa.Column("garmin_connection_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "imported_activities",
        sa.Column("activity_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "imported_activities",
        sa.Column("elevation_gain_meters", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE imported_activities ia
        SET garmin_connection_id = gc.id
        FROM garmin_connections gc
        WHERE ia.athlete_id = gc.athlete_id
        """
    )
    op.execute(
        """
        UPDATE imported_activities
        SET activity_date = (started_at AT TIME ZONE 'UTC')::date
        WHERE activity_date IS NULL
        """
    )

    op.alter_column("imported_activities", "garmin_connection_id", nullable=False)
    op.alter_column("imported_activities", "activity_date", nullable=False)

    op.create_foreign_key(
        "fk_imported_activities_garmin_connection_id",
        "imported_activities",
        "garmin_connections",
        ["garmin_connection_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "uq_imported_activities_athlete_garmin_id",
        "imported_activities",
        type_="unique",
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


def downgrade() -> None:
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
    op.create_unique_constraint(
        "uq_imported_activities_athlete_garmin_id",
        "imported_activities",
        ["athlete_id", "garmin_activity_id"],
    )
    op.drop_constraint(
        "fk_imported_activities_garmin_connection_id",
        "imported_activities",
        type_="foreignkey",
    )
    op.drop_column("imported_activities", "elevation_gain_meters")
    op.drop_column("imported_activities", "activity_date")
    op.drop_column("imported_activities", "garmin_connection_id")
