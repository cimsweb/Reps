from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DomainError,
    EmailAlreadyExistsError,
    InvalidEmailError,
    InvalidRoleError,
    UnauthenticatedError,
    WeakPasswordError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to HTTP error responses."""

    @app.exception_handler(InvalidEmailError)
    @app.exception_handler(WeakPasswordError)
    @app.exception_handler(InvalidRoleError)
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
    async def handle_authorization_error(_: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": str(exc)},
        )
