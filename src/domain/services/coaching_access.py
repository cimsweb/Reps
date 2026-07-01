"""Coaching data access rules between coaches and athletes."""

from domain.exceptions import AthleteDataAccessDeniedError, CoachAthleteAccessDeniedError
from domain.value_objects.user_id import UserId


def assert_athlete_owns_resource(actor_id: UserId, resource_athlete_id: UserId) -> None:
    """Raise when an athlete tries to access another athlete's data."""
    if actor_id != resource_athlete_id:
        raise AthleteDataAccessDeniedError("Athletes can only access their own coaching data")


def assert_coach_linked_to_athlete(
    coach_id: UserId,
    athlete_id: UserId,
    *,
    link_exists: bool,
) -> None:
    """Raise when a coach has no active link to the athlete."""
    if not link_exists:
        raise CoachAthleteAccessDeniedError(
            f"Coach {coach_id} is not linked to athlete {athlete_id}"
        )
