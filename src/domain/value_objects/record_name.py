from dataclasses import dataclass

from domain.exceptions import InvalidRecordNameError

_MAX_LENGTH = 128


@dataclass(frozen=True, slots=True)
class RecordName:
    """Name of a distance or exercise personal record."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidRecordNameError("Record name cannot be empty")
        if len(normalized) > _MAX_LENGTH:
            raise InvalidRecordNameError(f"Record name must be at most {_MAX_LENGTH} characters")
        object.__setattr__(self, "value", normalized)
