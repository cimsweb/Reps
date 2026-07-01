from typing import Protocol

from domain.entities.workout_feedback import WorkoutFeedback
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_feedback_id import WorkoutFeedbackId


class WorkoutFeedbackRepository(Protocol):
    """Persistence contract for workout feedback."""

    def save(self, feedback: WorkoutFeedback) -> WorkoutFeedback:
        """Persist workout feedback."""

    def get_by_id(self, feedback_id: WorkoutFeedbackId) -> WorkoutFeedback | None:
        """Load feedback by identifier."""

    def list_by_athlete(self, athlete_id: UserId) -> list[WorkoutFeedback]:
        """Return all feedback entries for an athlete."""

    def list_by_athlete_page(
        self,
        athlete_id: UserId,
        *,
        offset: int,
        limit: int,
    ) -> list[WorkoutFeedback]:
        """Return a page of feedback entries for an athlete."""

    def count_by_athlete(self, athlete_id: UserId) -> int:
        """Return total number of feedback entries for an athlete."""
