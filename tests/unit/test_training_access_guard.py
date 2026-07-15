"""Unit tests for TrainingAccessGuard."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.security.training_access_guard import TrainingAccessGuard
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.exceptions import TrainingAccessDeniedError
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryCoachAthleteLinkRepository


def test_training_access_guard_allows_linked_coach() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    links = InMemoryCoachAthleteLinkRepository()
    links.save(
        CoachAthleteLink(
            id=CoachAthleteLinkId(uuid4()),
            coach_id=coach_id,
            athlete_id=athlete_id,
            created_at=datetime.now(UTC),
        )
    )

    TrainingAccessGuard(links).ensure_coach_can_access_athlete_training(coach_id, athlete_id)


def test_training_access_guard_rejects_unlinked_coach() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        TrainingAccessGuard(
            InMemoryCoachAthleteLinkRepository()
        ).ensure_coach_can_access_athlete_training(UserId(uuid4()), UserId(uuid4()))


def test_training_access_guard_allows_athlete_owner() -> None:
    athlete_id = UserId(uuid4())
    TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()).ensure_athlete_owns_workout(
        athlete_id,
        athlete_id,
    )


def test_training_access_guard_rejects_other_athlete() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        TrainingAccessGuard(InMemoryCoachAthleteLinkRepository()).ensure_athlete_owns_workout(
            UserId(uuid4()),
            UserId(uuid4()),
        )


def test_training_access_guard_view_methods_delegate_to_write_checks() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    links = InMemoryCoachAthleteLinkRepository()
    links.save(
        CoachAthleteLink(
            id=CoachAthleteLinkId(uuid4()),
            coach_id=coach_id,
            athlete_id=athlete_id,
            created_at=datetime.now(UTC),
        )
    )
    guard = TrainingAccessGuard(links)

    guard.ensure_coach_can_view_athlete_training(coach_id, athlete_id)
    guard.ensure_athlete_can_view_own_training(athlete_id, athlete_id)


def test_training_access_guard_view_coach_rejects_unlinked_athlete() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        TrainingAccessGuard(
            InMemoryCoachAthleteLinkRepository()
        ).ensure_coach_can_view_athlete_training(UserId(uuid4()), UserId(uuid4()))
