from dataclasses import dataclass
from datetime import datetime

from domain.value_objects.difficulty_rating import DifficultyRating
from domain.value_objects.mood_rating import MoodRating
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_completion_report_id import WorkoutCompletionReportId


@dataclass(frozen=True, slots=True)
class WorkoutCompletionReport:
    """Athlete report after completing a planned workout."""

    id: WorkoutCompletionReportId
    planned_workout_id: PlannedWorkoutId
    athlete_id: UserId
    difficulty_rating: DifficultyRating
    mood_rating: MoodRating
    comment: str | None
    created_at: datetime
    garmin_url: str | None = None
    raw_report_text: str | None = None
