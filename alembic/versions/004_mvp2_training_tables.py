"""Create MVP 2 training tables.

Revision ID: 004
Revises: 003
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

plan_scope = postgresql.ENUM(
    "day",
    "week",
    name="plan_scope",
    create_type=False,
)
workout_type = postgresql.ENUM(
    "run",
    "bike",
    "gym",
    name="workout_type",
    create_type=False,
)


def upgrade() -> None:
    """Create training plan and report tables for MVP 2."""
    bind = op.get_bind()
    plan_scope.create(bind, checkfirst=True)
    workout_type.create(bind, checkfirst=True)

    op.create_table(
        "training_plans",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("coach_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("scope", plan_scope, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_training_plans_coach_id", "training_plans", ["coach_id"])
    op.create_index("ix_training_plans_athlete_id", "training_plans", ["athlete_id"])

    op.create_table(
        "planned_workouts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("plan_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("coach_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("workout_type", workout_type, nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["training_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_planned_workouts_plan_id", "planned_workouts", ["plan_id"])
    op.create_index("ix_planned_workouts_coach_id", "planned_workouts", ["coach_id"])
    op.create_index("ix_planned_workouts_athlete_id", "planned_workouts", ["athlete_id"])
    op.create_index("ix_planned_workouts_planned_date", "planned_workouts", ["planned_date"])
    op.create_index(
        "ix_planned_workouts_athlete_id_planned_date",
        "planned_workouts",
        ["athlete_id", "planned_date"],
    )
    op.create_index(
        "ix_planned_workouts_coach_id_planned_date",
        "planned_workouts",
        ["coach_id", "planned_date"],
    )

    op.create_table(
        "workout_cycles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("planned_workout_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["planned_workout_id"],
            ["planned_workouts.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_workout_cycles_planned_workout_id",
        "workout_cycles",
        ["planned_workout_id"],
    )

    op.create_table(
        "workout_exercises",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("cycle_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cycle_id"], ["workout_cycles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_workout_exercises_cycle_id", "workout_exercises", ["cycle_id"])

    op.create_table(
        "workout_completion_reports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("planned_workout_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("athlete_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("difficulty_rating", sa.Integer(), nullable=False),
        sa.Column("mood_rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["planned_workout_id"],
            ["planned_workouts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["athlete_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("planned_workout_id", name="uq_workout_completion_reports_workout"),
    )
    op.create_index(
        "ix_workout_completion_reports_athlete_id",
        "workout_completion_reports",
        ["athlete_id"],
    )
    op.create_index(
        "ix_workout_completion_reports_athlete_id_created_at",
        "workout_completion_reports",
        ["athlete_id", "created_at"],
    )


def downgrade() -> None:
    """Drop MVP 2 training tables."""
    op.drop_index(
        "ix_workout_completion_reports_athlete_id_created_at",
        table_name="workout_completion_reports",
    )
    op.drop_index(
        "ix_workout_completion_reports_athlete_id",
        table_name="workout_completion_reports",
    )
    op.drop_table("workout_completion_reports")
    op.drop_index("ix_workout_exercises_cycle_id", table_name="workout_exercises")
    op.drop_table("workout_exercises")
    op.drop_index("ix_workout_cycles_planned_workout_id", table_name="workout_cycles")
    op.drop_table("workout_cycles")
    op.drop_index("ix_planned_workouts_coach_id_planned_date", table_name="planned_workouts")
    op.drop_index("ix_planned_workouts_athlete_id_planned_date", table_name="planned_workouts")
    op.drop_index("ix_planned_workouts_planned_date", table_name="planned_workouts")
    op.drop_index("ix_planned_workouts_athlete_id", table_name="planned_workouts")
    op.drop_index("ix_planned_workouts_coach_id", table_name="planned_workouts")
    op.drop_index("ix_planned_workouts_plan_id", table_name="planned_workouts")
    op.drop_table("planned_workouts")
    op.drop_index("ix_training_plans_athlete_id", table_name="training_plans")
    op.drop_index("ix_training_plans_coach_id", table_name="training_plans")
    op.drop_table("training_plans")
    workout_type.drop(op.get_bind(), checkfirst=True)
    plan_scope.drop(op.get_bind(), checkfirst=True)
