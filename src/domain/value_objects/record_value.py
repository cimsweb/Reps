from dataclasses import dataclass

from domain.exceptions import InvalidPersonalRecordError

_MAX_LENGTH = 64


@dataclass(frozen=True, slots=True)
class RecordValue:
    """Measured value of a personal record."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidPersonalRecordError("Record value cannot be empty")
        if len(normalized) > _MAX_LENGTH:
            raise InvalidPersonalRecordError(
                f"Record value must be at most {_MAX_LENGTH} characters"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
