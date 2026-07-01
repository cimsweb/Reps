from typing import Annotated

from fastapi import APIRouter, Depends, Response

from application.dto.login_result import LoginResult
from application.use_cases.authenticate_session import AuthenticateSessionUseCase
from application.use_cases.get_current_user import GetCurrentUserUseCase
from application.use_cases.login_user import LoginUserUseCase
from application.use_cases.logout_user import LogoutUserUseCase
from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.role import Role
from domain.entities.user import User
from domain.services.authorization import Permission
from infrastructure.db.repositories import SqlAlchemySessionRepository, SqlAlchemyUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher
from interfaces.http.dependencies import (
    AuthorizationGuardDep,
    DbSession,
    get_bearer_token,
    get_password_hasher,
    get_session_token_service,
)
from interfaces.http.schemas import LoginRequest, LoginResponse, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=str(user.email),
        role=user.role.value,
        created_at=user.created_at,
    )


def _login_to_response(result: LoginResult) -> LoginResponse:
    return LoginResponse(
        token=result.token,
        expires_at=result.expires_at,
        user=_user_to_response(result.user),
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(
    body: RegisterRequest,
    db: DbSession,
    password_hasher: Annotated[ScryptPasswordHasher, Depends(get_password_hasher)],
) -> UserResponse:
    """Register a coach or athlete account."""
    user_repository = SqlAlchemyUserRepository(db)
    user = RegisterUserUseCase(user_repository, password_hasher).execute(
        body.email,
        body.password,
        Role.from_registration(body.role),
    )
    return _user_to_response(user)


@router.post("/login", response_model=LoginResponse)
def login_user(
    body: LoginRequest,
    db: DbSession,
    password_hasher: Annotated[ScryptPasswordHasher, Depends(get_password_hasher)],
) -> LoginResponse:
    """Authenticate and open a session."""
    user_repository = SqlAlchemyUserRepository(db)
    session_repository = SqlAlchemySessionRepository(db)
    token_service = get_session_token_service()
    result = LoginUserUseCase(
        user_repository,
        session_repository,
        password_hasher,
        token_service,
    ).execute(body.email, body.password)
    return _login_to_response(result)


@router.post("/logout", status_code=204)
def logout_user(
    db: DbSession,
    token: Annotated[str, Depends(get_bearer_token)],
) -> Response:
    """Terminate the current session."""
    user_repository = SqlAlchemyUserRepository(db)
    session_repository = SqlAlchemySessionRepository(db)
    authenticate = AuthenticateSessionUseCase(
        user_repository,
        session_repository,
        get_session_token_service(),
    )
    authenticated_user = authenticate.execute(token)
    LogoutUserUseCase(session_repository).execute(authenticated_user.session.id)
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
def get_current_user(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> UserResponse:
    """Return the authenticated user."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    user = GetCurrentUserUseCase(SqlAlchemyUserRepository(db)).execute(authenticated_user.user.id)
    return _user_to_response(user)
