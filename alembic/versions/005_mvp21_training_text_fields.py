"""Add MVP 2.1 text fields to training tables.

Revision ID: 005
Revises: 004
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("training_plans", sa.Column("raw_text", sa.Text(), nullable=True))
    op.add_column(
        "workout_completion_reports",
        sa.Column("garmin_url", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "workout_completion_reports",
        sa.Column("raw_report_text", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workout_completion_reports", "raw_report_text")
    op.drop_column("workout_completion_reports", "garmin_url")
    op.drop_column("training_plans", "raw_text")
