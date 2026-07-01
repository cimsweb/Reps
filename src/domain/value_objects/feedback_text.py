from dataclasses import dataclass

from domain.exceptions import InvalidFeedbackTextError

_MAX_LENGTH = 5000


@dataclass(frozen=True, slots=True)
class FeedbackText:
    """Validated workout feedback text."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidFeedbackTextError("Feedback text cannot be empty")
        if len(normalized) > _MAX_LENGTH:
            raise InvalidFeedbackTextError(
                f"Feedback text must be at most {_MAX_LENGTH} characters"
            )
        object.__setattr__(self, "value", normalized)
