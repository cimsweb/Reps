import logging
from datetime import UTC, datetime
from uuid import uuid4

from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import DomainError, EmailAlreadyExistsError, InvalidRoleError
from domain.repositories.user_repository import UserRepository
from domain.services.auth import PasswordHasher
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.plain_password import PlainPassword
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_auth_event


class RegisterUserUseCase:
    """Register a new user account."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        logger: logging.Logger | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._logger = logger or logging.getLogger("reps.auth")

    def execute(self, email: str, password: str, role: Role) -> User:
        """Create a user with validated credentials."""
        try:
            validated_email = Email(email)
            PlainPassword(password)
            if role is Role.ADMIN:
                raise InvalidRoleError("Admin role cannot be assigned during registration")

            existing_user = self._user_repository.get_by_email(validated_email)
            if existing_user is not None:
                raise EmailAlreadyExistsError(f"Email already exists: {validated_email}")

            password_hash = PasswordHash(self._password_hasher.hash(password))
            user = User(
                id=UserId(uuid4()),
                email=validated_email,
                password_hash=password_hash,
                role=role,
                created_at=datetime.now(UTC),
            )
            saved_user = self._user_repository.save(user)
        except DomainError as error:
            log_auth_event(
                self._logger,
                event="register",
                success=False,
                message=str(error),
            )
            raise

        log_auth_event(
            self._logger,
            event="register",
            success=True,
            user_id=str(saved_user.id),
            role=saved_user.role.value,
            message="User registered",
        )
        return saved_user
