"""Tests for RegisterUserUseCase."""

import pytest

from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.role import Role
from domain.exceptions import EmailAlreadyExistsError, InvalidRoleError, WeakPasswordError
from fakes.in_memory_repositories import InMemoryUserRepository
from infrastructure.security.scrypt_password_hasher import ScryptPasswordHasher


def test_register_user_creates_hashed_password() -> None:
    repository = InMemoryUserRepository()
    use_case = RegisterUserUseCase(repository, ScryptPasswordHasher())

    user = use_case.execute("coach@example.com", "secure1A", Role.COACH)

    assert str(user.email) == "coach@example.com"
    assert str(user.password_hash) != "secure1A"
    assert user.role is Role.COACH


def test_register_user_rejects_duplicate_email() -> None:
    repository = InMemoryUserRepository()
    use_case = RegisterUserUseCase(repository, ScryptPasswordHasher())
    use_case.execute("coach@example.com", "secure1A", Role.COACH)

    with pytest.raises(EmailAlreadyExistsError):
        use_case.execute("coach@example.com", "another1A", Role.ATHLETE)


def test_register_user_rejects_weak_password() -> None:
    repository = InMemoryUserRepository()
    use_case = RegisterUserUseCase(repository, ScryptPasswordHasher())

    with pytest.raises(WeakPasswordError):
        use_case.execute("coach@example.com", "weak", Role.COACH)


def test_register_user_rejects_admin_role() -> None:
    repository = InMemoryUserRepository()
    use_case = RegisterUserUseCase(repository, ScryptPasswordHasher())

    with pytest.raises(InvalidRoleError):
        use_case.execute("admin@example.com", "secure1A", Role.ADMIN)
