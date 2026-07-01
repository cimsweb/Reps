from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class WorkoutFeedbackId:
    """Unique workout feedback identifier."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)
