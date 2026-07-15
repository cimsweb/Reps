"""Tests for MoodRating value object."""

import pytest

from domain.exceptions import InvalidMoodRatingError
from domain.value_objects.mood_rating import MoodRating


def test_mood_rating_accepts_valid_range() -> None:
    assert MoodRating(0).value == 0
    assert MoodRating(10).value == 10


@pytest.mark.parametrize("invalid_value", [-1, 11, 100])
def test_mood_rating_rejects_out_of_range(invalid_value: int) -> None:
    with pytest.raises(InvalidMoodRatingError):
        MoodRating(invalid_value)
