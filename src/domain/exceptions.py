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


class TrainingPlanNotFoundError(DomainError):
    """Raised when training plan does not exist."""


class PlannedWorkoutNotFoundError(DomainError):
    """Raised when planned workout does not exist."""


class WorkoutCompletionReportNotFoundError(DomainError):
    """Raised when workout completion report does not exist."""


class InvalidDifficultyRatingError(DomainError):
    """Raised when difficulty rating is outside 0–10."""


class InvalidMoodRatingError(DomainError):
    """Raised when mood rating is outside 0–10."""


class WorkoutReportAlreadyExistsError(DomainError):
    """Raised when a report already exists for the planned workout."""


class DuplicatePlannedWorkoutError(DomainError):
    """Raised when a workout already exists for coach, athlete and date."""


class TrainingAccessDeniedError(DomainError):
    """Raised when user has no access to training plan or report data."""


class InvalidTrainingPlanError(DomainError):
    """Raised when training plan payload is invalid."""


class InvalidWorkoutStructureError(DomainError):
    """Raised when workout cycles or exercises are invalid."""


class PastWorkoutModificationError(DomainError):
    """Raised when coach tries to modify a workout in the past."""


class TrainingTextParsingNotAvailableError(DomainError):
    """Raised when text parsing is requested but parser is not configured."""


class AgentAssistantNotAvailableError(DomainError):
    """Raised when AI agent dialog is requested but not implemented yet."""


class AgentSessionNotFoundError(DomainError):
    """Raised when agent session does not exist."""


class AgentSessionExpiredError(DomainError):
    """Raised when agent session exceeded inactivity expiry."""


class AgentSessionMessageLimitError(DomainError):
    """Raised when agent session reached the message limit."""


class AgentSessionNotActiveError(DomainError):
    """Raised when operation requires an active agent session."""


class AIServiceUnavailableError(DomainError):
    """Raised when AI provider is not configured or unreachable."""


class AIResponseInvalidError(DomainError):
    """Raised when AI provider returned an invalid response."""


class DuplicateActiveReportAgentSessionError(DomainError):
    """Raised when an active report agent session already exists for the workout."""


class ConversationNotFoundError(DomainError):
    """Raised when conversation does not exist."""


class InvalidConversationMessageContentError(DomainError):
    """Raised when conversation message content is invalid."""
