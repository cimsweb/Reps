from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CoachAthleteLinkId:
    """Unique coach-athlete link identifier."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)
