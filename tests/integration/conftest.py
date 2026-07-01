"""Shared helpers for integration tests."""

import os

import pytest
from sqlalchemy import create_engine, text

from infrastructure.db.engine import get_database_url


def database_is_available() -> bool:
    database_url = os.getenv("DATABASE_URL", get_database_url())
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


@pytest.fixture
def requires_postgres() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")
