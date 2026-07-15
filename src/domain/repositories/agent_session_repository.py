from datetime import datetime
from typing import Protocol

from domain.entities.agent_session import AgentSession
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId


class AgentSessionRepository(Protocol):
    """Persistence contract for agent dialog sessions."""

    def save(self, session: AgentSession) -> AgentSession:
        """Persist an agent session."""

    def get_by_id(self, session_id: AgentSessionId) -> AgentSession | None:
        """Load agent session by identifier."""

    def get_active_report_session(
        self,
        planned_workout_id: PlannedWorkoutId,
    ) -> AgentSession | None:
        """Return active report assistance session for a workout, if any."""

    def list_active_by_coach(self, coach_id: UserId) -> list[AgentSession]:
        """Return active plan-creation sessions for a coach."""

    def list_active_by_athlete(self, athlete_id: UserId) -> list[AgentSession]:
        """Return active sessions for an athlete."""

    def get_active_plan_session_for_coach_athlete(
        self,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> AgentSession | None:
        """Return the latest active plan-creation session for coach and athlete."""

    def complete(self, session_id: AgentSessionId, *, now: datetime | None = None) -> AgentSession:
        """Mark session as completed."""

    def abandon(self, session_id: AgentSessionId, *, now: datetime | None = None) -> AgentSession:
        """Mark session as abandoned."""

    def abandon_expired_active_sessions(self, *, now: datetime | None = None) -> int:
        """Mark expired active sessions as abandoned. Returns count updated."""
