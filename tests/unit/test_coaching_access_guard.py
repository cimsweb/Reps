"""Unit tests for CoachingAccessGuard."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.security.coaching_access_guard import CoachingAccessGuard
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.exceptions import AthleteDataAccessDeniedError, CoachAthleteAccessDeniedError
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryCoachAthleteLinkRepository


def test_coaching_access_guard_allows_linked_coach() -> None:
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

    CoachingAccessGuard(links).ensure_coach_can_access_athlete(coach_id, athlete_id)


def test_coaching_access_guard_rejects_unlinked_coach() -> None:
    with pytest.raises(CoachAthleteAccessDeniedError):
        CoachingAccessGuard(InMemoryCoachAthleteLinkRepository()).ensure_coach_can_access_athlete(
            UserId(uuid4()),
            UserId(uuid4()),
        )


def test_coaching_access_guard_allows_athlete_owner() -> None:
    athlete_id = UserId(uuid4())
    CoachingAccessGuard(InMemoryCoachAthleteLinkRepository()).ensure_athlete_owns_data(
        athlete_id,
        athlete_id,
    )


def test_coaching_access_guard_rejects_other_athlete() -> None:
    with pytest.raises(AthleteDataAccessDeniedError):
        CoachingAccessGuard(InMemoryCoachAthleteLinkRepository()).ensure_athlete_owns_data(
            UserId(uuid4()),
            UserId(uuid4()),
        )
