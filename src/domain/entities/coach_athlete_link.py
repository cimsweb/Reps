from dataclasses import dataclass
from datetime import datetime

from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class CoachAthleteLink:
    """Established coaching relationship between coach and athlete."""

    id: CoachAthleteLinkId
    coach_id: UserId
    athlete_id: UserId
    created_at: datetime
