from dataclasses import dataclass
from datetime import date, datetime

from domain.entities.agent_session_kind import AgentSessionKind
from domain.entities.agent_session_status import AgentSessionStatus
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class AgentSession:
    """AI-assisted dialog session for plan creation or report assistance."""

    id: AgentSessionId
    kind: AgentSessionKind
    coach_id: UserId | None
    athlete_id: UserId
    planned_workout_id: PlannedWorkoutId | None
    status: AgentSessionStatus
    start_date: date | None
    created_at: datetime
    updated_at: datetime
