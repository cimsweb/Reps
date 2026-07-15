from dataclasses import dataclass
from datetime import date, datetime

from domain.entities.plan_scope import PlanScope
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class TrainingPlan:
    """Coach-authored training plan for an athlete."""

    id: TrainingPlanId
    coach_id: UserId
    athlete_id: UserId
    scope: PlanScope
    start_date: date
    created_at: datetime
    raw_text: str | None = None
