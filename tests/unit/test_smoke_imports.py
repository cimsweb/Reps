"""Smoke tests for package imports."""

import importlib

MODULES = [
    "domain",
    "domain.entities.user",
    "domain.entities.session",
    "domain.entities.role",
    "domain.value_objects.plain_password",
    "domain.services.auth",
    "domain.services.authorization",
    "domain.repositories.user_repository",
    "domain.repositories.session_repository",
    "application.use_cases.register_user",
    "application.use_cases.login_user",
    "application.use_cases.logout_user",
    "application.use_cases.get_current_user",
    "application.use_cases.list_users",
    "application.use_cases.authenticate_session",
    "application.security.authorization_guard",
    "application.dto.user_queries",
    "domain.value_objects.pagination",
    "infrastructure.logging.setup",
    "infrastructure.db.models",
    "infrastructure.db.repositories",
    "infrastructure.db.seed_admin",
    "infrastructure.db.engine",
    "infrastructure.security.scrypt_password_hasher",
    "infrastructure.security.sha256_session_token",
    "interfaces.http",
]


def test_all_modules_import_cleanly() -> None:
    for module_name in MODULES:
        importlib.import_module(module_name)
