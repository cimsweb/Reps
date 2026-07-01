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

    invitation_indexes = {index["name"] for index in inspector.get_indexes("invitations")}
    personal_record_indexes = {index["name"] for index in inspector.get_indexes("personal_records")}
    feedback_indexes = {index["name"] for index in inspector.get_indexes("workout_feedback")}

    assert "ix_invitations_coach_id_status" in invitation_indexes
    assert "ix_personal_records_athlete_id_record_type" in personal_record_indexes
    assert "ix_workout_feedback_athlete_id_created_at" in feedback_indexes
