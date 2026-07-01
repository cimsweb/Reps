from dataclasses import dataclass

from domain.exceptions import InvalidProfileDataError

_MIN_AGE = 10
_MAX_AGE = 100


@dataclass(frozen=True, slots=True)
class Age:
    """Athlete age in full years."""

    value: int

    def __post_init__(self) -> None:
        if self.value < _MIN_AGE or self.value > _MAX_AGE:
            raise InvalidProfileDataError(f"Age must be between {_MIN_AGE} and {_MAX_AGE}")
