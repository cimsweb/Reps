#!/usr/bin/env python3
"""Delete abandoned agent sessions older than retention policy."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from application.services.agent_session_cleanup import ABANDONED_SESSION_RETENTION_DAYS
from domain.entities.agent_session_status import AgentSessionStatus
from infrastructure.config.env import load_environment
from infrastructure.db.engine import create_db_engine
from infrastructure.db.models import AgentSessionRecord


def delete_old_abandoned_sessions(
    db_session: Session,
    *,
    retention_days: int = ABANDONED_SESSION_RETENTION_DAYS,
) -> int:
    threshold = datetime.now(UTC) - timedelta(days=retention_days)
    stmt = (
        delete(AgentSessionRecord)
        .where(
            AgentSessionRecord.status == AgentSessionStatus.ABANDONED,
            AgentSessionRecord.updated_at < threshold,
        )
        .returning(AgentSessionRecord.id)
    )
    deleted_ids = list(db_session.scalars(stmt).all())
    db_session.commit()
    return len(deleted_ids)


def main() -> None:
    load_environment()
    engine = create_db_engine()
    with Session(engine) as db_session:
        count = delete_old_abandoned_sessions(db_session)
    print(f"Deleted {count} abandoned agent sessions")


if __name__ == "__main__":
    main()
