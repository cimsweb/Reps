from dataclasses import dataclass

from domain.exceptions import InvalidProfileDataError

_MIN_HEIGHT_CM = 100
_MAX_HEIGHT_CM = 250


@dataclass(frozen=True, slots=True)
class HeightCm:
    """Athlete height in centimeters."""

    value: int

    def __post_init__(self) -> None:
        if self.value < _MIN_HEIGHT_CM or self.value > _MAX_HEIGHT_CM:
            raise InvalidProfileDataError(
                f"Height must be between {_MIN_HEIGHT_CM} and {_MAX_HEIGHT_CM} cm"
            )
