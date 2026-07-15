"""Query use cases for MVP 2.2 AI agent sessions."""

from dataclasses import dataclass
from datetime import date, datetime

from application.dto.agent import AgentSessionView
from application.security.training_access_guard import TrainingAccessGuard
from application.services.agent_dialog_helpers import (
    enrich_plan_draft_reply,
    load_athlete_report_session_for_view,
    load_coach_plan_session_for_view,
)
from application.services.agent_session_cleanup import run_lazy_agent_session_cleanup
from application.services.agent_session_presenter import (
    build_session_view,
    rebuild_latest_reply,
)
from domain.entities.agent_session import AgentSession
from domain.exceptions import AgentSessionNotFoundError, PlannedWorkoutNotFoundError
from domain.repositories.agent_message_repository import AgentMessageRepository
from domain.repositories.agent_session_repository import AgentSessionRepository
from domain.repositories.planned_workout_repository import PlannedWorkoutRepository
from domain.services.agent_assistant_reply import AgentPlanDraftReply
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class AgentSessionSummaryView:
    session_id: AgentSessionId
    athlete_id: UserId
    kind: str
    status: str
    updated_at: datetime


def _build_view_from_session(
    session: AgentSession,
    messages: list,
) -> AgentSessionView:
    latest_reply = rebuild_latest_reply(messages)
    start_date = session.start_date or date.today()
    if isinstance(latest_reply, AgentPlanDraftReply):
        latest_reply = enrich_plan_draft_reply(latest_reply, start_date=start_date)
    return build_session_view(
        session_id=session.id,
        kind=session.kind.value,
        status=session.status.value,
        messages=messages,
        latest_reply=latest_reply,
    )


class GetPlanAgentSessionUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._access_guard = access_guard

    def execute(
        self,
        *,
        coach_id: UserId,
        session_id: AgentSessionId,
    ) -> AgentSessionView:
        session = load_coach_plan_session_for_view(
            self._session_repository,
            session_id,
            coach_id,
        )
        self._access_guard.ensure_coach_can_view_athlete_training(coach_id, session.athlete_id)
        messages = self._message_repository.list_by_session(session.id)
        return _build_view_from_session(session, messages)


class GetReportAgentSessionUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._access_guard = access_guard

    def execute(
        self,
        *,
        athlete_id: UserId,
        session_id: AgentSessionId,
    ) -> AgentSessionView:
        session = load_athlete_report_session_for_view(
            self._session_repository,
            session_id,
            athlete_id,
        )
        self._access_guard.ensure_athlete_can_view_own_training(athlete_id, session.athlete_id)
        messages = self._message_repository.list_by_session(session.id)
        return _build_view_from_session(session, messages)


class GetActivePlanAgentSessionForAthleteUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._access_guard = access_guard

    def execute(
        self,
        *,
        coach_id: UserId,
        athlete_id: UserId,
    ) -> AgentSessionView:
        self._access_guard.ensure_coach_can_view_athlete_training(coach_id, athlete_id)
        run_lazy_agent_session_cleanup(self._session_repository)
        session = self._session_repository.get_active_plan_session_for_coach_athlete(
            coach_id,
            athlete_id,
        )
        if session is None:
            raise AgentSessionNotFoundError(
                f"No active plan agent session for athlete: {athlete_id}"
            )
        messages = self._message_repository.list_by_session(session.id)
        return _build_view_from_session(session, messages)


class GetActiveReportAgentSessionForWorkoutUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        workout_repository: PlannedWorkoutRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._workout_repository = workout_repository
        self._access_guard = access_guard

    def execute(
        self,
        *,
        athlete_id: UserId,
        planned_workout_id: PlannedWorkoutId,
    ) -> AgentSessionView:
        workout = self._workout_repository.get_by_id(planned_workout_id)
        if workout is None:
            raise PlannedWorkoutNotFoundError(f"Planned workout not found: {planned_workout_id}")
        self._access_guard.ensure_athlete_owns_workout(athlete_id, workout.athlete_id)
        run_lazy_agent_session_cleanup(self._session_repository)
        session = self._session_repository.get_active_report_session(planned_workout_id)
        if session is None:
            raise AgentSessionNotFoundError(
                f"No active report agent session for workout: {planned_workout_id}"
            )
        messages = self._message_repository.list_by_session(session.id)
        return _build_view_from_session(session, messages)


class ListCoachActiveAgentSessionsUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        access_guard: TrainingAccessGuard,
    ) -> None:
        self._session_repository = session_repository
        self._access_guard = access_guard

    def execute(
        self,
        *,
        coach_id: UserId,
        athlete_id: UserId | None = None,
    ) -> tuple[AgentSessionSummaryView, ...]:
        run_lazy_agent_session_cleanup(self._session_repository)
        sessions = self._session_repository.list_active_by_coach(coach_id)
        summaries: list[AgentSessionSummaryView] = []
        for session in sessions:
            if athlete_id is not None and session.athlete_id != athlete_id:
                continue
            self._access_guard.ensure_coach_can_view_athlete_training(
                coach_id,
                session.athlete_id,
            )
            summaries.append(
                AgentSessionSummaryView(
                    session_id=session.id,
                    athlete_id=session.athlete_id,
                    kind=session.kind.value,
                    status=session.status.value,
                    updated_at=session.updated_at,
                )
            )
        return tuple(summaries)
