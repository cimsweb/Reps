from datetime import date

from domain.exceptions import PastWorkoutModificationError, TrainingAccessDeniedError
from domain.value_objects.user_id import UserId


def assert_athlete_owns_workout(actor_id: UserId, athlete_id: UserId) -> None:
    """Verify the athlete acts on their own training data."""
    if actor_id != athlete_id:
        raise TrainingAccessDeniedError("Athlete can only access their own workouts")


def assert_coach_linked_to_athlete(
    coach_id: UserId,
    athlete_id: UserId,
    *,
    link_exists: bool,
) -> None:
    """Verify the coach is linked to the athlete."""
    if not link_exists:
        raise TrainingAccessDeniedError("Coach is not linked to this athlete")


def assert_workout_not_in_past(planned_date: date, today: date) -> None:
    """Verify the workout date is today or in the future."""
    if planned_date < today:
        raise PastWorkoutModificationError("Cannot modify workouts scheduled in the past")
