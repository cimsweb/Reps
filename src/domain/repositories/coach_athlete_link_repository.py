from typing import Protocol

from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.value_objects.user_id import UserId


class CoachAthleteLinkRepository(Protocol):
    """Persistence contract for coach-athlete relationships."""

    def save(self, link: CoachAthleteLink) -> CoachAthleteLink:
        """Persist a coach-athlete link."""

    def exists(self, coach_id: UserId, athlete_id: UserId) -> bool:
        """Return whether a link already exists."""

    def get_by_coach_and_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> CoachAthleteLink | None:
        """Load link for a coach and athlete pair."""

    def list_by_coach(self, coach_id: UserId) -> list[CoachAthleteLink]:
        """Return all athletes linked to a coach."""

    def list_by_athlete(self, athlete_id: UserId) -> list[CoachAthleteLink]:
        """Return all coaches linked to an athlete."""

    def count_by_coach(self, coach_id: UserId) -> int:
        """Return number of athletes linked to a coach."""
