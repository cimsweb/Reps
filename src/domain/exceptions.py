"""Domain-level exceptions."""


class DomainError(Exception):
    """Base exception for domain rule violations."""


class InvalidEmailError(DomainError):
    """Raised when email format is invalid."""


class InvalidRoleError(DomainError):
    """Raised when role value is not allowed."""


class WeakPasswordError(DomainError):
    """Raised when password does not meet policy requirements."""


class EmailAlreadyExistsError(DomainError):
    """Raised when email is already registered."""


class AuthenticationError(DomainError):
    """Raised when credentials are invalid."""


class UnauthenticatedError(DomainError):
    """Raised when session token is missing, invalid, or expired."""


class AuthorizationError(DomainError):
    """Raised when user lacks permission for an action."""
