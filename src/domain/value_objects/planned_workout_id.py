from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PlannedWorkoutId:
    """Unique planned workout identifier."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)
