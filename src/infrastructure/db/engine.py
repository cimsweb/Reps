import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql+psycopg://reps:reps@localhost:5432/reps"


def get_database_url() -> str:
    """Return database URL from environment or default."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_db_engine(database_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine."""
    return create_engine(database_url or get_database_url(), pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to an engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
