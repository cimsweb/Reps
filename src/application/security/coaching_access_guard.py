import logging
from collections.abc import Callable

from domain.exceptions import DomainError
from domain.repositories.coach_athlete_link_repository import CoachAthleteLinkRepository
from domain.services.coaching_access import (
    assert_athlete_owns_resource,
    assert_coach_linked_to_athlete,
)
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_coaching_event


class CoachingAccessGuard:
    """Enforce coach-athlete data ownership and link-based access."""

    def __init__(
        self,
        link_repository: CoachAthleteLinkRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._link_repository = link_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def ensure_athlete_owns_data(self, actor_id: UserId, athlete_id: UserId) -> None:
        """Verify the athlete accesses only their own coaching data."""
        self._enforce(lambda: assert_athlete_owns_resource(actor_id, athlete_id), actor_id)

    def ensure_coach_can_access_athlete(self, coach_id: UserId, athlete_id: UserId) -> None:
        """Verify the coach is linked to the athlete."""
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
            log_coaching_event(
                self._logger,
                "coaching_authorization_error",
                success=False,
                user_id=str(actor_id),
                message=str(error),
            )
            raise
