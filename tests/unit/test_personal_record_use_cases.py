"""Tests for personal record use cases."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.use_cases.personal_record_commands import (
    CreatePersonalRecordUseCase,
    DeletePersonalRecordUseCase,
    UpdatePersonalRecordUseCase,
)
from domain.entities.role import Role
from domain.exceptions import (
    AuthorizationError,
    PersonalRecordNotFoundError,
    RecordOwnershipError,
)
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryPersonalRecordRepository


def _achieved_at() -> datetime:
    return datetime(2026, 6, 1, 8, 0, tzinfo=UTC)


def test_create_personal_record_saves_record() -> None:
    repository = InMemoryPersonalRecordRepository()
    athlete_id = UserId(uuid4())
    use_case = CreatePersonalRecordUseCase(repository)

    record = use_case.execute(
        athlete_id,
        Role.ATHLETE,
        "distance",
        "5K",
        "19:45",
        "time",
        _achieved_at(),
    )

    assert record.name == "5K"
    assert str(record.value) == "19:45"


def test_update_personal_record_changes_fields() -> None:
    repository = InMemoryPersonalRecordRepository()
    athlete_id = UserId(uuid4())
    create_use_case = CreatePersonalRecordUseCase(repository)
    created = create_use_case.execute(
        athlete_id,
        Role.ATHLETE,
        "distance",
        "5K",
        "19:45",
        "time",
        _achieved_at(),
    )

    updated = UpdatePersonalRecordUseCase(repository).execute(
        athlete_id,
        Role.ATHLETE,
        str(created.id),
        "distance",
        "10K",
        "40:00",
        "time",
        _achieved_at(),
    )

    assert updated.name == "10K"
    assert str(updated.value) == "40:00"


def test_delete_personal_record_removes_record() -> None:
    repository = InMemoryPersonalRecordRepository()
    athlete_id = UserId(uuid4())
    created = CreatePersonalRecordUseCase(repository).execute(
        athlete_id,
        Role.ATHLETE,
        "exercise",
        "Pull-ups",
        "20",
        "reps",
        _achieved_at(),
    )

    DeletePersonalRecordUseCase(repository).execute(
        athlete_id,
        Role.ATHLETE,
        str(created.id),
    )

    assert repository.get_by_id(created.id) is None


def test_update_personal_record_rejects_foreign_record() -> None:
    repository = InMemoryPersonalRecordRepository()
    owner_id = UserId(uuid4())
    other_id = UserId(uuid4())
    created = CreatePersonalRecordUseCase(repository).execute(
        owner_id,
        Role.ATHLETE,
        "distance",
        "5K",
        "19:45",
        "time",
        _achieved_at(),
    )

    with pytest.raises(RecordOwnershipError):
        UpdatePersonalRecordUseCase(repository).execute(
            other_id,
            Role.ATHLETE,
            str(created.id),
            "distance",
            "10K",
            "40:00",
            "time",
            _achieved_at(),
        )


def test_delete_personal_record_rejects_missing_record() -> None:
    with pytest.raises(PersonalRecordNotFoundError):
        DeletePersonalRecordUseCase(InMemoryPersonalRecordRepository()).execute(
            UserId(uuid4()),
            Role.ATHLETE,
            str(uuid4()),
        )


def test_create_personal_record_rejects_coach_role() -> None:
    with pytest.raises(AuthorizationError):
        CreatePersonalRecordUseCase(InMemoryPersonalRecordRepository()).execute(
            UserId(uuid4()),
            Role.COACH,
            "distance",
            "5K",
            "19:45",
            "time",
            _achieved_at(),
        )
