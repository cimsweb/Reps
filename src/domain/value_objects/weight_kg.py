from dataclasses import dataclass

from domain.exceptions import InvalidProfileDataError

_MIN_WEIGHT_KG = 30
_MAX_WEIGHT_KG = 300


@dataclass(frozen=True, slots=True)
class WeightKg:
    """Athlete weight in kilograms."""

    value: int

    def __post_init__(self) -> None:
        if self.value < _MIN_WEIGHT_KG or self.value > _MAX_WEIGHT_KG:
            raise InvalidProfileDataError(
                f"Weight must be between {_MIN_WEIGHT_KG} and {_MAX_WEIGHT_KG} kg"
            )
