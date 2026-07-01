import logging
from datetime import UTC, datetime
from uuid import uuid4

from domain.entities.role import Role
from domain.entities.workout_feedback import WorkoutFeedback
from domain.exceptions import AuthorizationError, DomainError
from domain.repositories.workout_feedback_repository import WorkoutFeedbackRepository
from domain.value_objects.feedback_text import FeedbackText
from domain.value_objects.garmin_report_url import GarminReportUrl
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_feedback_id import WorkoutFeedbackId
from infrastructure.logging.setup import log_coaching_event


class SubmitWorkoutFeedbackUseCase:
    """Athlete submits workout feedback with optional Garmin link."""

    def __init__(
        self,
        feedback_repository: WorkoutFeedbackRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._feedback_repository = feedback_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        text: str,
        garmin_url: str | None = None,
    ) -> WorkoutFeedback:
        """Save workout feedback for the athlete."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can submit workout feedback")

            validated_garmin_url = GarminReportUrl(garmin_url) if garmin_url else None
            feedback = WorkoutFeedback(
                id=WorkoutFeedbackId(uuid4()),
                athlete_id=athlete_id,
                text=FeedbackText(text).value,
                garmin_url=validated_garmin_url,
                created_at=datetime.now(UTC),
            )
            saved_feedback = self._feedback_repository.save(feedback)
        except DomainError as error:
            log_coaching_event(
                self._logger,
                "coaching_validation_error",
                success=False,
                user_id=str(athlete_id),
                message=str(error),
            )
            raise

        log_coaching_event(
            self._logger,
            "workout_feedback_submitted",
            success=True,
            user_id=str(athlete_id),
            message="Workout feedback submitted",
        )
        return saved_feedback
