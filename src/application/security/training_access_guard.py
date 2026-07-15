import logging
from collections.abc import Callable

from domain.exceptions import DomainError
from domain.repositories.coach_athlete_link_repository import CoachAthleteLinkRepository
from domain.services.training_access import (
    assert_athlete_owns_workout,
    assert_coach_linked_to_athlete,
)
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_training_event


class TrainingAccessGuard:
    """Enforce coach-athlete access to training plans and reports."""

    def __init__(
        self,
        link_repository: CoachAthleteLinkRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._link_repository = link_repository
        self._logger = logger or logging.getLogger("reps.training")

    def ensure_athlete_owns_workout(self, actor_id: UserId, athlete_id: UserId) -> None:
        """Verify the athlete accesses only their own training data."""
        self._enforce(lambda: assert_athlete_owns_workout(actor_id, athlete_id), actor_id)

    def ensure_athlete_can_view_own_training(self, actor_id: UserId, athlete_id: UserId) -> None:
        """Verify the athlete reads only their own training data."""
        self.ensure_athlete_owns_workout(actor_id, athlete_id)

    def ensure_coach_can_access_athlete_training(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> None:
        """Verify the coach is linked to the athlete for write operations."""
        self._ensure_coach_linked(coach_id, athlete_id)

    def ensure_coach_can_view_athlete_training(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> None:
        """Verify the coach reads training data only for linked athletes."""
        self._ensure_coach_linked(coach_id, athlete_id)

    def _ensure_coach_linked(self, coach_id: UserId, athlete_id: UserId) -> None:
        link_exists = self._link_repository.exists(coach_id, athlete_id)
        self._enforce(
            lambda: assert_coach_linked_to_athlete(
                coach_id,
                athlete_id,
                link_exists=link_exists,
            ),
            coach_id,
        )

    def _enforce(self, rule: Callable[[], None], actor_id: UserId) -> None:
        try:
            rule()
        except DomainError as error:
            log_training_event(
                self._logger,
                "training_authorization_error",
                success=False,
                user_id=str(actor_id),
                message=str(error),
            )
            raise
