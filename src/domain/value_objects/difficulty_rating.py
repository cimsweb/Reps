from dataclasses import dataclass

from domain.exceptions import InvalidDifficultyRatingError

_MIN_RATING = 0
_MAX_RATING = 10


@dataclass(frozen=True, slots=True)
class DifficultyRating:
    """Workout difficulty on a 0–10 scale (10 is hardest)."""

    value: int

    def __post_init__(self) -> None:
        if self.value < _MIN_RATING or self.value > _MAX_RATING:
            raise InvalidDifficultyRatingError(
                f"Difficulty rating must be between {_MIN_RATING} and {_MAX_RATING}"
            )
