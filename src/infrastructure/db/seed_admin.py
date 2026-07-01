import os
from datetime import UTC, datetime
from uuid import uuid4

from domain.entities.role import Role
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from domain.services.auth import PasswordHasher
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId


def seed_admin_user(
    user_repository: UserRepository,
    password_hasher: PasswordHasher,
    *,
    email: str | None = None,
    password: str | None = None,
) -> User | None:
    """Create the initial admin user when it does not exist yet."""
    return upsert_admin_user(
        user_repository,
        password_hasher,
        email=email,
        password=password,
        create_only=True,
    )


def upsert_admin_user(
    user_repository: UserRepository,
    password_hasher: PasswordHasher,
    *,
    email: str | None = None,
    password: str | None = None,
    create_only: bool = False,
) -> User | None:
    """Create or update the admin user from environment variables."""
    admin_email_value = email if email is not None else os.getenv("ADMIN_EMAIL", "admin@reps.local")
    admin_email = Email(admin_email_value)
    admin_password = password or os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD environment variable is required")

    existing_admin = user_repository.get_by_email(admin_email)
    if existing_admin is not None:
        if create_only:
            return None
        updated_admin = User(
            id=existing_admin.id,
            email=existing_admin.email,
            password_hash=PasswordHash(password_hasher.hash(admin_password)),
            role=Role.ADMIN,
            created_at=existing_admin.created_at,
        )
        return user_repository.save(updated_admin)

    admin_user = User(
        id=UserId(uuid4()),
        email=admin_email,
        password_hash=PasswordHash(password_hasher.hash(admin_password)),
        role=Role.ADMIN,
        created_at=datetime.now(UTC),
    )
    return user_repository.save(admin_user)
