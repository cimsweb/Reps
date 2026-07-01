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


@pytest.fixture(autouse=True)
def isolate_admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep admin integration tests independent from developer .env values."""
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)


@pytest.fixture
def requires_postgres() -> None:
    if not database_is_available():
        pytest.skip("PostgreSQL is not available")
