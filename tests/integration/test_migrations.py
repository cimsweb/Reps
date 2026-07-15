"""Integration tests for database migrations."""

import subprocess
import sys

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import create_engine

from infrastructure.db.engine import get_database_url
from integration.conftest import database_is_available


@pytest.mark.integration
def test_migrations_apply_on_clean_database() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    engine = create_engine(get_database_url())
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert "users" in tables
    assert "sessions" in tables
    assert "invitations" in tables
    assert "coach_athlete_links" in tables
    assert "athlete_profiles" in tables
    assert "personal_records" in tables
    assert "workout_feedback" in tables
    assert "training_plans" in tables
    assert "planned_workouts" in tables
    assert "workout_cycles" in tables
    assert "workout_exercises" in tables
    assert "workout_completion_reports" in tables
    assert "agent_sessions" in tables
    assert "agent_messages" in tables
    assert "garmin_connections" not in tables
    assert "imported_activities" not in tables
    assert "sync_jobs" not in tables
    assert "conversations" in tables
    assert "conversation_messages" in tables

    session_indexes = {index["name"] for index in inspector.get_indexes("agent_sessions")}
    message_indexes = {index["name"] for index in inspector.get_indexes("agent_messages")}
    assert "ix_agent_sessions_coach_id_status" in session_indexes
    assert "uq_agent_sessions_active_report_per_workout" in session_indexes
    assert "ix_agent_messages_session_id_sort_order" in message_indexes

    invitation_indexes = {index["name"] for index in inspector.get_indexes("invitations")}
    personal_record_indexes = {index["name"] for index in inspector.get_indexes("personal_records")}
    feedback_indexes = {index["name"] for index in inspector.get_indexes("workout_feedback")}

    planned_workout_indexes = {index["name"] for index in inspector.get_indexes("planned_workouts")}
    report_indexes = {
        index["name"] for index in inspector.get_indexes("workout_completion_reports")
    }

    assert "ix_invitations_coach_id_status" in invitation_indexes
    assert "ix_personal_records_athlete_id_record_type" in personal_record_indexes
    assert "ix_workout_feedback_athlete_id_created_at" in feedback_indexes
    assert "ix_planned_workouts_athlete_id_planned_date" in planned_workout_indexes
    assert "ix_planned_workouts_coach_id_planned_date" in planned_workout_indexes
    assert "ix_workout_completion_reports_athlete_id_created_at" in report_indexes

    report_uniques = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("workout_completion_reports")
    }
    assert "uq_workout_completion_reports_workout" in report_uniques
