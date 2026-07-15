from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import (
    AgentAssistantNotAvailableError,
    AgentSessionExpiredError,
    AgentSessionMessageLimitError,
    AgentSessionNotActiveError,
    AgentSessionNotFoundError,
    AIResponseInvalidError,
    AIServiceUnavailableError,
    AthleteDataAccessDeniedError,
    AthleteProfileNotFoundError,
    AuthenticationError,
    AuthorizationError,
    CoachAthleteAccessDeniedError,
    CoachAthleteLinkAlreadyExistsError,
    ConversationNotFoundError,
    DomainError,
    DuplicateActiveReportAgentSessionError,
    DuplicateInvitationError,
    DuplicatePlannedWorkoutError,
    EmailAlreadyExistsError,
    InvalidConversationMessageContentError,
    InvalidDifficultyRatingError,
    InvalidEmailError,
    InvalidFeedbackTextError,
    InvalidGarminUrlError,
    InvalidInvitationTargetError,
    InvalidMoodRatingError,
    InvalidPersonalRecordError,
    InvalidProfileDataError,
    InvalidRecordNameError,
    InvalidRoleError,
    InvalidTrainingPlanError,
    InvalidWorkoutStructureError,
    InvitationAlreadyRespondedError,
    InvitationEmailMismatchError,
    InvitationNotFoundError,
    PastWorkoutModificationError,
    PersonalRecordNotFoundError,
    PlannedWorkoutNotFoundError,
    RecordOwnershipError,
    TrainingAccessDeniedError,
    TrainingPlanNotFoundError,
    TrainingTextParsingNotAvailableError,
    UnauthenticatedError,
    WeakPasswordError,
    WorkoutCompletionReportNotFoundError,
    WorkoutReportAlreadyExistsError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to HTTP error responses."""

    @app.exception_handler(InvalidEmailError)
    @app.exception_handler(WeakPasswordError)
    @app.exception_handler(InvalidRoleError)
    @app.exception_handler(InvalidProfileDataError)
    @app.exception_handler(InvalidPersonalRecordError)
    @app.exception_handler(InvalidGarminUrlError)
    @app.exception_handler(InvalidFeedbackTextError)
    @app.exception_handler(InvalidConversationMessageContentError)
    @app.exception_handler(InvalidRecordNameError)
    @app.exception_handler(InvalidInvitationTargetError)
    @app.exception_handler(InvitationEmailMismatchError)
    @app.exception_handler(InvitationAlreadyRespondedError)
    @app.exception_handler(RecordOwnershipError)
    @app.exception_handler(InvalidTrainingPlanError)
    @app.exception_handler(InvalidWorkoutStructureError)
    @app.exception_handler(InvalidDifficultyRatingError)
    @app.exception_handler(InvalidMoodRatingError)
    @app.exception_handler(PastWorkoutModificationError)
    async def handle_validation_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "validation_error", "message": str(exc)},
        )

    @app.exception_handler(TrainingTextParsingNotAvailableError)
    @app.exception_handler(AgentAssistantNotAvailableError)
    async def handle_not_implemented(
        _: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content={"error": "not_implemented", "message": str(exc)},
        )

    @app.exception_handler(AIServiceUnavailableError)
    async def handle_ai_unavailable(
        _: Request,
        exc: AIServiceUnavailableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": "ai_unavailable",
                "message": str(exc),
                "fallback": "manual",
            },
        )

    @app.exception_handler(AgentSessionNotActiveError)
    async def handle_agent_session_not_active(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "conflict", "message": str(exc)},
        )

    @app.exception_handler(AgentSessionMessageLimitError)
    async def handle_agent_message_limit(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": "message_limit", "message": str(exc)},
        )

    @app.exception_handler(AgentSessionExpiredError)
    async def handle_agent_session_expired(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=410,
            content={"error": "session_expired", "message": str(exc)},
        )

    @app.exception_handler(AIResponseInvalidError)
    async def handle_ai_response_invalid(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"error": "ai_response_invalid", "message": str(exc)},
        )

    @app.exception_handler(EmailAlreadyExistsError)
    async def handle_email_exists(_: Request, exc: EmailAlreadyExistsError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "email_already_exists", "message": str(exc)},
        )

    @app.exception_handler(DuplicateInvitationError)
    @app.exception_handler(CoachAthleteLinkAlreadyExistsError)
    @app.exception_handler(DuplicatePlannedWorkoutError)
    @app.exception_handler(WorkoutReportAlreadyExistsError)
    @app.exception_handler(DuplicateActiveReportAgentSessionError)
    async def handle_conflict(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "conflict", "message": str(exc)},
        )

    @app.exception_handler(AthleteProfileNotFoundError)
    @app.exception_handler(InvitationNotFoundError)
    @app.exception_handler(PersonalRecordNotFoundError)
    @app.exception_handler(PlannedWorkoutNotFoundError)
    @app.exception_handler(TrainingPlanNotFoundError)
    @app.exception_handler(WorkoutCompletionReportNotFoundError)
    @app.exception_handler(AgentSessionNotFoundError)
    @app.exception_handler(ConversationNotFoundError)
    async def handle_not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": str(exc)},
        )

    @app.exception_handler(AuthenticationError)
    async def handle_authentication_error(_: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error": "invalid_credentials", "message": str(exc)},
        )

    @app.exception_handler(UnauthenticatedError)
    async def handle_unauthenticated(_: Request, exc: UnauthenticatedError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthenticated", "message": str(exc)},
        )

    @app.exception_handler(AuthorizationError)
    @app.exception_handler(CoachAthleteAccessDeniedError)
    @app.exception_handler(AthleteDataAccessDeniedError)
    @app.exception_handler(TrainingAccessDeniedError)
    async def handle_authorization_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": str(exc)},
        )
