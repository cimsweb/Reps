from typing import Annotated

from fastapi import APIRouter, Depends, Query

from application.use_cases.list_users import ListUsersUseCase
from domain.services.authorization import Permission
from domain.value_objects.pagination import PageRequest
from infrastructure.db.repositories import SqlAlchemyUserRepository
from interfaces.http.dependencies import AuthorizationGuardDep, DbSession, get_bearer_token
from interfaces.http.schemas import UserListResponse, UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserListResponse:
    """List all users. Admin only."""
    guard.authorize(token, Permission.LIST_USERS)
    result = ListUsersUseCase(SqlAlchemyUserRepository(db)).execute(
        PageRequest(offset=offset, limit=limit)
    )
    return UserListResponse(
        items=[
            UserResponse(
                id=str(profile.id),
                email=profile.email,
                role=profile.role.value,
                created_at=profile.created_at,
            )
            for profile in result.items
        ],
        total=result.total,
    )
