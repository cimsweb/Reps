"""Unit tests for training access rules."""

from datetime import date
from uuid import uuid4

import pytest

from domain.exceptions import PastWorkoutModificationError, TrainingAccessDeniedError
from domain.services.training_access import (
    assert_athlete_owns_workout,
    assert_coach_linked_to_athlete,
    assert_workout_not_in_past,
)
from domain.value_objects.user_id import UserId


def test_assert_athlete_owns_workout_allows_owner() -> None:
    athlete_id = UserId(uuid4())
    assert_athlete_owns_workout(athlete_id, athlete_id)


def test_assert_athlete_owns_workout_rejects_other_athlete() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        assert_athlete_owns_workout(UserId(uuid4()), UserId(uuid4()))


def test_assert_coach_linked_to_athlete_allows_existing_link() -> None:
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    assert_coach_linked_to_athlete(coach_id, athlete_id, link_exists=True)


def test_assert_coach_linked_to_athlete_rejects_missing_link() -> None:
    with pytest.raises(TrainingAccessDeniedError):
        assert_coach_linked_to_athlete(UserId(uuid4()), UserId(uuid4()), link_exists=False)


def test_assert_workout_not_in_past_allows_today_and_future() -> None:
    today = date(2026, 6, 26)
    assert_workout_not_in_past(today, today)
    assert_workout_not_in_past(date(2026, 6, 27), today)


def test_assert_workout_not_in_past_rejects_past_date() -> None:
    with pytest.raises(PastWorkoutModificationError):
        assert_workout_not_in_past(date(2026, 6, 25), date(2026, 6, 26))
