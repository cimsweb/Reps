"""Tests for DifficultyRating value object."""

import pytest

from domain.exceptions import InvalidDifficultyRatingError
from domain.value_objects.difficulty_rating import DifficultyRating


def test_difficulty_rating_accepts_valid_range() -> None:
    assert DifficultyRating(0).value == 0
    assert DifficultyRating(10).value == 10


@pytest.mark.parametrize("invalid_value", [-1, 11, 100])
def test_difficulty_rating_rejects_out_of_range(invalid_value: int) -> None:
    with pytest.raises(InvalidDifficultyRatingError):
        DifficultyRating(invalid_value)
