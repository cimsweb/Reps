from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import (
    AthleteDataAccessDeniedError,
    AthleteProfileNotFoundError,
    AuthenticationError,
    AuthorizationError,
    CoachAthleteAccessDeniedError,
    CoachAthleteLinkAlreadyExistsError,
    DomainError,
    DuplicateInvitationError,
    EmailAlreadyExistsError,
    InvalidEmailError,
    InvalidFeedbackTextError,
    InvalidGarminUrlError,
    InvalidInvitationTargetError,
    InvalidPersonalRecordError,
    InvalidProfileDataError,
    InvalidRecordNameError,
    InvalidRoleError,
    InvitationAlreadyRespondedError,
    InvitationEmailMismatchError,
    InvitationNotFoundError,
    PersonalRecordNotFoundError,
    RecordOwnershipError,
    UnauthenticatedError,
    WeakPasswordError,
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
    @app.exception_handler(InvalidRecordNameError)
    @app.exception_handler(InvalidInvitationTargetError)
    @app.exception_handler(InvitationEmailMismatchError)
    @app.exception_handler(InvitationAlreadyRespondedError)
    @app.exception_handler(RecordOwnershipError)
    async def handle_validation_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "validation_error", "message": str(exc)},
        )

    @app.exception_handler(EmailAlreadyExistsError)
    async def handle_email_exists(_: Request, exc: EmailAlreadyExistsError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "email_already_exists", "message": str(exc)},
        )

    @app.exception_handler(DuplicateInvitationError)
    @app.exception_handler(CoachAthleteLinkAlreadyExistsError)
    async def handle_conflict(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error": "conflict", "message": str(exc)},
        )

    @app.exception_handler(AthleteProfileNotFoundError)
    @app.exception_handler(InvitationNotFoundError)
    @app.exception_handler(PersonalRecordNotFoundError)
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
    async def handle_authorization_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": str(exc)},
        )
