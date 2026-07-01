"""Unit tests for coaching access rules."""

from uuid import uuid4

import pytest

from domain.exceptions import AthleteDataAccessDeniedError, CoachAthleteAccessDeniedError
from domain.services.coaching_access import (
    assert_athlete_owns_resource,
    assert_coach_linked_to_athlete,
)
from domain.value_objects.user_id import UserId


def test_assert_athlete_owns_resource_allows_owner() -> None:
    athlete_id = UserId(uuid4())
    assert_athlete_owns_resource(athlete_id, athlete_id)


def test_assert_athlete_owns_resource_rejects_other_athlete() -> None:
    with pytest.raises(AthleteDataAccessDeniedError):
        assert_athlete_owns_resource(UserId(uuid4()), UserId(uuid4()))


def test_assert_coach_linked_to_athlete_allows_existing_link() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    assert_coach_linked_to_athlete(coach_id, athlete_id, link_exists=True)


def test_assert_coach_linked_to_athlete_rejects_missing_link() -> None:
    with pytest.raises(CoachAthleteAccessDeniedError):
        assert_coach_linked_to_athlete(UserId(uuid4()), UserId(uuid4()), link_exists=False)
