from datetime import datetime
from typing import Protocol

from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_completion_report_id import WorkoutCompletionReportId


class WorkoutCompletionReportRepository(Protocol):
    """Persistence contract for workout completion reports."""

    def save(self, report: WorkoutCompletionReport) -> WorkoutCompletionReport:
        """Persist a workout completion report."""

    def get_by_id(self, report_id: WorkoutCompletionReportId) -> WorkoutCompletionReport | None:
        """Load report by identifier."""

    def get_by_planned_workout(
        self,
        planned_workout_id: PlannedWorkoutId,
    ) -> WorkoutCompletionReport | None:
        """Load report for a planned workout if it exists."""

    def list_by_athlete_and_date_range(
        self,
        athlete_id: UserId,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WorkoutCompletionReport]:
        """Return athlete reports created within a datetime range."""
