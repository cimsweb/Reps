from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PersonalRecordId:
    """Unique personal record identifier."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)
