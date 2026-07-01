"""Tests for LogoutUserUseCase."""

from datetime import UTC, datetime
from uuid import uuid4

from application.use_cases.logout_user import LogoutUserUseCase
from domain.entities.session import Session
from domain.value_objects.session_id import SessionId
from domain.value_objects.user_id import UserId
from fakes.in_memory_repositories import InMemorySessionRepository


def test_logout_user_deletes_existing_session() -> None:
    repository = InMemorySessionRepository()
    session_id = SessionId(uuid4())
    repository.save(
        Session(
            id=session_id,
            user_id=UserId(uuid4()),
            token_hash="hash",
            expires_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
    )

    LogoutUserUseCase(repository).execute(session_id)

    assert repository.get_by_id(session_id) is None


def test_logout_user_ignores_missing_session() -> None:
    repository = InMemorySessionRepository()

    LogoutUserUseCase(repository).execute(SessionId(uuid4()))

    assert repository.get_by_id(SessionId(uuid4())) is None
