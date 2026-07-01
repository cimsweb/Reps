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


class InvitationNotFoundError(DomainError):
    """Raised when invitation does not exist."""


class InvitationAlreadyRespondedError(DomainError):
    """Raised when invitation was already accepted or declined."""


class DuplicateInvitationError(DomainError):
    """Raised when a pending invitation already exists for the same coach and email."""


class CoachAthleteLinkAlreadyExistsError(DomainError):
    """Raised when coach and athlete are already linked."""


class AthleteProfileNotFoundError(DomainError):
    """Raised when athlete profile does not exist."""


class InvalidProfileDataError(DomainError):
    """Raised when athlete profile fields are invalid."""


class PersonalRecordNotFoundError(DomainError):
    """Raised when personal record does not exist."""


class InvalidPersonalRecordError(DomainError):
    """Raised when personal record fields are invalid."""


class InvalidGarminUrlError(DomainError):
    """Raised when Garmin Connect URL is invalid."""


class WorkoutFeedbackNotFoundError(DomainError):
    """Raised when workout feedback does not exist."""


class CoachAthleteAccessDeniedError(DomainError):
    """Raised when coach has no access to athlete data."""


class AthleteDataAccessDeniedError(DomainError):
    """Raised when athlete tries to access another athlete's data."""


class InvalidFeedbackTextError(DomainError):
    """Raised when workout feedback text is invalid."""


class InvalidRecordNameError(DomainError):
    """Raised when personal record name is invalid."""


class InvitationEmailMismatchError(DomainError):
    """Raised when athlete email does not match the invitation."""


class InvalidInvitationTargetError(DomainError):
    """Raised when invitation target is not a valid athlete email."""


class RecordOwnershipError(DomainError):
    """Raised when athlete tries to modify another athlete's record."""
