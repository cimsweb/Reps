from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserId:
    """Unique user identifier."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)
