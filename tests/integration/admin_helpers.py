"""Admin helpers for integration tests."""

from uuid import uuid4

from application.dto.login_result import LoginResult
from application.use_cases.login_user import LoginUserUseCase
from domain.entities.user import User
from domain.services.auth import PasswordHasher
from infrastructure.db.repositories import SqlAlchemySessionRepository, SqlAlchemyUserRepository
from infrastructure.db.seed_admin import seed_admin_user
from infrastructure.security.sha256_session_token import Sha256SessionTokenService

TEST_ADMIN_PASSWORD = "secure1Admin"


def create_test_admin_email() -> str:
    """Return a unique admin email for an integration test."""
    return f"admin-test-{uuid4()}@example.com"


def seed_test_admin(
    user_repository: SqlAlchemyUserRepository,
    password_hasher: PasswordHasher,
    email: str,
) -> User:
    """Create an admin user with explicit test credentials."""
    admin_user = seed_admin_user(
        user_repository,
        password_hasher,
        email=email,
        password=TEST_ADMIN_PASSWORD,
    )
    if admin_user is None:
        raise RuntimeError(f"Failed to seed test admin for {email}")
    return admin_user


def login_test_admin(
    user_repository: SqlAlchemyUserRepository,
    session_repository: SqlAlchemySessionRepository,
    password_hasher: PasswordHasher,
    token_service: Sha256SessionTokenService,
    email: str,
) -> LoginResult:
    """Authenticate a seeded test admin."""
    return LoginUserUseCase(
        user_repository,
        session_repository,
        password_hasher,
        token_service,
    ).execute(email, TEST_ADMIN_PASSWORD)
