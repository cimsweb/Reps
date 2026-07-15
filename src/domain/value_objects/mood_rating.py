from dataclasses import dataclass

from domain.exceptions import InvalidMoodRatingError

_MIN_RATING = 0
_MAX_RATING = 10


@dataclass(frozen=True, slots=True)
class MoodRating:
    """Emotional state on a 0–10 scale (10 is best)."""

    value: int

    def __post_init__(self) -> None:
        if self.value < _MIN_RATING or self.value > _MAX_RATING:
            raise InvalidMoodRatingError(
                f"Mood rating must be between {_MIN_RATING} and {_MAX_RATING}"
            )
