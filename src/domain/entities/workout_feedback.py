from dataclasses import dataclass
from datetime import datetime

from domain.value_objects.garmin_report_url import GarminReportUrl
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_feedback_id import WorkoutFeedbackId


@dataclass(frozen=True, slots=True)
class WorkoutFeedback:
    """Athlete feedback after a workout, optionally with a Garmin report link."""

    id: WorkoutFeedbackId
    athlete_id: UserId
    text: str
    garmin_url: GarminReportUrl | None
    created_at: datetime
