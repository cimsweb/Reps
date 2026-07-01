from dataclasses import dataclass
from datetime import datetime

from domain.entities.gender import Gender
from domain.value_objects.age import Age
from domain.value_objects.height_cm import HeightCm
from domain.value_objects.user_id import UserId
from domain.value_objects.weight_kg import WeightKg


@dataclass(frozen=True, slots=True)
class AthleteProfile:
    """Physical profile data for an athlete."""

    athlete_id: UserId
    height_cm: HeightCm
    weight_kg: WeightKg
    age: Age
    gender: Gender
    updated_at: datetime
