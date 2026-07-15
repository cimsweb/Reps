from typing import Protocol

from domain.entities.training_plan import TrainingPlan
from domain.value_objects.training_plan_id import TrainingPlanId


class TrainingPlanRepository(Protocol):
    """Persistence contract for training plans."""

    def save(self, plan: TrainingPlan) -> TrainingPlan:
        """Persist a training plan."""

    def get_by_id(self, plan_id: TrainingPlanId) -> TrainingPlan | None:
        """Load training plan by identifier."""
