from typing import Protocol

from domain.entities.athlete_profile import AthleteProfile
from domain.value_objects.user_id import UserId


class AthleteProfileRepository(Protocol):
    """Persistence contract for athlete profiles."""

    def save(self, profile: AthleteProfile) -> AthleteProfile:
        """Persist an athlete profile."""

    def get_by_athlete_id(self, athlete_id: UserId) -> AthleteProfile | None:
        """Load profile for an athlete."""
