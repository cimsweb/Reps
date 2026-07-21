"""AI agent dialog use cases (MVP 2.2-002)."""

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

from application.dto.agent import AgentSessionView
from application.dto.ai import AiProviderCredentials
from application.ports.ai_service import AIService
from application.security.training_access_guard import TrainingAccessGuard
from application.services.agent_dialog_helpers import (
    append_assistant_message,
    append_user_message,
    build_chat_messages,
    build_plan_system_prompt,
    build_report_system_prompt,
    enrich_plan_draft_reply,
    ensure_message_limit,
    invoke_plan_agent_ai,
    invoke_report_agent_ai,
    load_athlete_report_session,
    load_coach_plan_session,
    log_ai_event,
    touch_session,
)
from application.services.agent_session_cleanup import run_lazy_agent_session_cleanup
from application.services.agent_session_presenter import (
    build_session_view,
    extract_latest_plan_draft,
    extract_latest_report_draft,
    rebuild_latest_reply,
)
from application.services.agent_workout_context import format_workout_context
from application.use_cases.training_commands import SubmitWorkoutCompletionReportUseCase
from application.use_cases.training_text_commands import CreateTrainingPlanFromTextUseCase
from domain.entities.agent_session import AgentSession
from domain.entities.agent_session_kind import AgentSessionKind
from domain.entities.agent_session_status import AgentSessionStatus
from domain.entities.role import Role
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.exceptions import (
    AgentSessionNotActiveError,
    InvalidDifficultyRatingError,
    InvalidMoodRatingError,
)
from domain.repositories.agent_message_repository import AgentMessageRepository
from domain.repositories.agent_session_repository import AgentSessionRepository
from domain.repositories.planned_workout_repository import PlannedWorkoutRepository
from domain.repositories.training_plan_repository import TrainingPlanRepository
from domain.repositories.workout_completion_report_repository import (
    WorkoutCompletionReportRepository,
)
from domain.repositories.workout_cycle_repository import WorkoutCycleRepository
from domain.repositories.workout_exercise_repository import WorkoutExerciseRepository
from domain.services.agent_assistant_reply import (
    AgentPlanDraftReply,
    AgentReportDraftReply,
    TrainingPlanDraft,
)
from domain.value_objects.agent_session_id import AgentSessionId
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.user_id import UserId
from infrastructure.ai.ai_service_factory import build_ai_service


@dataclass(frozen=True, slots=True)
class ConfirmPlanAgentDraftResult:
    plan: TrainingPlan


@dataclass(frozen=True, slots=True)
class ConfirmReportAgentDraftResult:
    report: WorkoutCompletionReport


class StartPlanAgentSessionUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.ai")

    def execute(
        self,
        *,
        coach_id: UserId,
        athlete_id: UserId,
        start_date: date,
        initial_brief: str | None = None,
        ai_credentials: AiProviderCredentials | None = None,
    ) -> AgentSessionView:
        self._access_guard.ensure_coach_can_access_athlete_training(coach_id, athlete_id)
        run_lazy_agent_session_cleanup(self._session_repository)
        now = datetime.now(UTC)
        session = self._session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.PLAN_CREATION,
                coach_id=coach_id,
                athlete_id=athlete_id,
                planned_workout_id=None,
                status=AgentSessionStatus.ACTIVE,
                start_date=start_date,
                created_at=now,
                updated_at=now,
            )
        )
        log_ai_event(
            self._logger,
            "ai_session_started",
            session_id=str(session.id),
            kind=session.kind.value,
            user_id=str(coach_id),
            content=initial_brief,
        )
        if initial_brief:
            return SendPlanAgentMessageUseCase(
                session_repository=self._session_repository,
                message_repository=self._message_repository,
                access_guard=self._access_guard,
                logger=self._logger,
            ).execute(
                coach_id=coach_id,
                session_id=session.id,
                content=initial_brief,
                ai_credentials=ai_credentials,
            )
        return build_session_view(
            session_id=session.id,
            kind=session.kind.value,
            status=session.status.value,
            messages=[],
            latest_reply=None,
        )


class SendPlanAgentMessageUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        access_guard: TrainingAccessGuard,
        ai_service: AIService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._access_guard = access_guard
        self._ai_service = ai_service
        self._logger = logger or logging.getLogger("reps.ai")

    def execute(
        self,
        *,
        coach_id: UserId,
        session_id: AgentSessionId,
        content: str,
        ai_credentials: AiProviderCredentials | None = None,
    ) -> AgentSessionView:
        session = load_coach_plan_session(self._session_repository, session_id, coach_id)
        self._access_guard.ensure_coach_can_access_athlete_training(coach_id, session.athlete_id)
        messages = self._message_repository.list_by_session(session.id)
        ensure_message_limit(messages)

        sort_order = len(messages)
        append_user_message(
            self._message_repository,
            session=session,
            content=content,
            sort_order=sort_order,
        )
        messages = self._message_repository.list_by_session(session.id)
        session = self._session_repository.save(touch_session(session))

        system_prompt = build_plan_system_prompt(
            athlete_id=session.athlete_id,
            start_date=session.start_date or date.today(),
        )
        chat_messages = build_chat_messages(system_prompt=system_prompt, history=messages)
        ai_service = self._ai_service or build_ai_service(
            AgentSessionKind.PLAN_CREATION,
            credentials=ai_credentials,
        )
        reply = invoke_plan_agent_ai(ai_service, chat_messages)
        reply = enrich_plan_draft_reply(reply, start_date=session.start_date or date.today())

        append_assistant_message(
            self._message_repository,
            session=session,
            reply=reply,
            sort_order=len(messages),
        )
        messages = self._message_repository.list_by_session(session.id)
        session = self._session_repository.save(touch_session(session))

        log_ai_event(
            self._logger,
            "ai_message_sent",
            session_id=str(session.id),
            kind=session.kind.value,
            user_id=str(coach_id),
            content=content,
        )
        if isinstance(reply, AgentPlanDraftReply):
            log_ai_event(
                self._logger,
                "ai_draft_proposed",
                session_id=str(session.id),
                kind=session.kind.value,
                user_id=str(coach_id),
            )

        return build_session_view(
            session_id=session.id,
            kind=session.kind.value,
            status=session.status.value,
            messages=messages,
            latest_reply=reply,
        )


class ConfirmPlanAgentDraftUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        plan_repository: TrainingPlanRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._create_plan = CreateTrainingPlanFromTextUseCase(
            plan_repository=plan_repository,
            workout_repository=workout_repository,
            cycle_repository=cycle_repository,
            exercise_repository=exercise_repository,
            access_guard=access_guard,
        )
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.ai")

    def execute(
        self,
        *,
        coach_id: UserId,
        session_id: AgentSessionId,
        draft_override: TrainingPlanDraft | None = None,
    ) -> ConfirmPlanAgentDraftResult:
        session = load_coach_plan_session(self._session_repository, session_id, coach_id)
        messages = self._message_repository.list_by_session(session.id)
        draft = draft_override or extract_latest_plan_draft(messages)
        if draft is None or not draft.raw_text:
            raise AgentSessionNotActiveError("No plan draft available to confirm")

        plan = self._create_plan.execute(
            coach_id=coach_id,
            coach_role=Role.COACH,
            athlete_id=session.athlete_id,
            scope=draft.scope,
            start_date=draft.start_date,
            text=draft.raw_text,
        )
        self._session_repository.complete(session.id)
        log_ai_event(
            self._logger,
            "ai_confirmed",
            session_id=str(session.id),
            kind=session.kind.value,
            user_id=str(coach_id),
        )
        return ConfirmPlanAgentDraftResult(plan=plan)


class StartReportAgentSessionUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        report_repository: WorkoutCompletionReportRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._report_repository = report_repository
        self._access_guard = access_guard
        self._logger = logger or logging.getLogger("reps.ai")

    def execute(
        self,
        *,
        athlete_id: UserId,
        planned_workout_id: PlannedWorkoutId,
    ) -> AgentSessionView:
        workout = self._workout_repository.get_by_id(planned_workout_id)
        if workout is None:
            from domain.exceptions import PlannedWorkoutNotFoundError

            raise PlannedWorkoutNotFoundError(f"Planned workout not found: {planned_workout_id}")
        self._access_guard.ensure_athlete_owns_workout(athlete_id, workout.athlete_id)
        run_lazy_agent_session_cleanup(self._session_repository)
        if self._report_repository.get_by_planned_workout(planned_workout_id) is not None:
            from domain.exceptions import WorkoutReportAlreadyExistsError

            raise WorkoutReportAlreadyExistsError(
                f"Report already exists for workout: {planned_workout_id}"
            )

        existing = self._session_repository.get_active_report_session(planned_workout_id)
        if existing is not None:
            messages = self._message_repository.list_by_session(existing.id)
            return build_session_view(
                session_id=existing.id,
                kind=existing.kind.value,
                status=existing.status.value,
                messages=messages,
                latest_reply=rebuild_latest_reply(messages),
            )

        now = datetime.now(UTC)
        session = self._session_repository.save(
            AgentSession(
                id=AgentSessionId(uuid4()),
                kind=AgentSessionKind.REPORT_ASSISTANCE,
                coach_id=None,
                athlete_id=athlete_id,
                planned_workout_id=planned_workout_id,
                status=AgentSessionStatus.ACTIVE,
                start_date=None,
                created_at=now,
                updated_at=now,
            )
        )
        log_ai_event(
            self._logger,
            "ai_session_started",
            session_id=str(session.id),
            kind=session.kind.value,
            user_id=str(athlete_id),
        )
        return build_session_view(
            session_id=session.id,
            kind=session.kind.value,
            status=session.status.value,
            messages=[],
            latest_reply=None,
        )


class SendReportAgentMessageUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        workout_repository: PlannedWorkoutRepository,
        cycle_repository: WorkoutCycleRepository,
        exercise_repository: WorkoutExerciseRepository,
        access_guard: TrainingAccessGuard,
        ai_service: AIService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._workout_repository = workout_repository
        self._cycle_repository = cycle_repository
        self._exercise_repository = exercise_repository
        self._access_guard = access_guard
        self._ai_service = ai_service
        self._logger = logger or logging.getLogger("reps.ai")

    def execute(
        self,
        *,
        athlete_id: UserId,
        session_id: AgentSessionId,
        content: str,
        ai_credentials: AiProviderCredentials | None = None,
    ) -> AgentSessionView:
        session = load_athlete_report_session(self._session_repository, session_id, athlete_id)
        workout_id = session.planned_workout_id
        if workout_id is None:
            raise AgentSessionNotActiveError("Report session has no planned workout")
        workout = self._workout_repository.get_by_id(workout_id)
        if workout is None:
            from domain.exceptions import PlannedWorkoutNotFoundError

            raise PlannedWorkoutNotFoundError(f"Planned workout not found: {workout_id}")
        self._access_guard.ensure_athlete_owns_workout(athlete_id, workout.athlete_id)

        messages = self._message_repository.list_by_session(session.id)
        ensure_message_limit(messages)
        append_user_message(
            self._message_repository,
            session=session,
            content=content,
            sort_order=len(messages),
        )
        messages = self._message_repository.list_by_session(session.id)
        session = self._session_repository.save(touch_session(session))

        workout_context = format_workout_context(
            workout,
            self._cycle_repository,
            self._exercise_repository,
        )
        chat_messages = build_chat_messages(
            system_prompt=build_report_system_prompt(workout_context=workout_context),
            history=messages,
        )
        ai_service = self._ai_service or build_ai_service(
            AgentSessionKind.REPORT_ASSISTANCE,
            credentials=ai_credentials,
        )
        reply = invoke_report_agent_ai(ai_service, chat_messages)
        append_assistant_message(
            self._message_repository,
            session=session,
            reply=reply,
            sort_order=len(messages),
        )
        messages = self._message_repository.list_by_session(session.id)
        session = self._session_repository.save(touch_session(session))

        log_ai_event(
            self._logger,
            "ai_message_sent",
            session_id=str(session.id),
            kind=session.kind.value,
            user_id=str(athlete_id),
            content=content,
        )
        if isinstance(reply, AgentReportDraftReply):
            log_ai_event(
                self._logger,
                "ai_draft_proposed",
                session_id=str(session.id),
                kind=session.kind.value,
                user_id=str(athlete_id),
            )

        return build_session_view(
            session_id=session.id,
            kind=session.kind.value,
            status=session.status.value,
            messages=messages,
            latest_reply=reply,
        )


class ConfirmReportAgentDraftUseCase:
    def __init__(
        self,
        *,
        session_repository: AgentSessionRepository,
        message_repository: AgentMessageRepository,
        workout_repository: PlannedWorkoutRepository,
        report_repository: WorkoutCompletionReportRepository,
        access_guard: TrainingAccessGuard,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session_repository = session_repository
        self._message_repository = message_repository
        self._submit_report = SubmitWorkoutCompletionReportUseCase(
            workout_repository,
            report_repository,
            access_guard,
        )
        self._logger = logger or logging.getLogger("reps.ai")

    def execute(
        self,
        *,
        athlete_id: UserId,
        session_id: AgentSessionId,
        difficulty_rating: int | None = None,
        mood_rating: int | None = None,
        comment: str | None = None,
        garmin_url: str | None = None,
        raw_report_text: str | None = None,
    ) -> ConfirmReportAgentDraftResult:
        session = load_athlete_report_session(self._session_repository, session_id, athlete_id)
        messages = self._message_repository.list_by_session(session.id)
        draft = extract_latest_report_draft(messages)
        if draft is None:
            raise AgentSessionNotActiveError("No report draft available to confirm")

        final_difficulty = difficulty_rating
        if final_difficulty is None:
            final_difficulty = draft.suggested_difficulty_rating
        final_mood = mood_rating if mood_rating is not None else draft.suggested_mood_rating
        if final_difficulty is None or final_mood is None:
            raise InvalidDifficultyRatingError(
                "Difficulty and mood ratings are required to confirm"
            )
        if not 0 <= final_difficulty <= 10:
            raise InvalidDifficultyRatingError("Difficulty rating must be between 0 and 10")
        if not 0 <= final_mood <= 10:
            raise InvalidMoodRatingError("Mood rating must be between 0 and 10")

        workout_id = session.planned_workout_id
        if workout_id is None:
            raise AgentSessionNotActiveError("Report session has no planned workout")

        report = self._submit_report.execute(
            athlete_id,
            Role.ATHLETE,
            str(workout_id.value),
            final_difficulty,
            final_mood,
            comment or draft.comment_body,
            garmin_url or (str(draft.garmin_url) if draft.garmin_url else None),
            raw_report_text,
        )
        self._session_repository.complete(session.id)
        log_ai_event(
            self._logger,
            "ai_confirmed",
            session_id=str(session.id),
            kind=session.kind.value,
            user_id=str(athlete_id),
        )
        return ConfirmReportAgentDraftResult(report=report)
