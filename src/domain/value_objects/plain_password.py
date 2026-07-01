import re
from dataclasses import dataclass

from domain.exceptions import WeakPasswordError

_MIN_LENGTH = 8
_MAX_LENGTH = 128
_LETTER_PATTERN = re.compile(r"[A-Za-z]")
_DIGIT_PATTERN = re.compile(r"\d")


@dataclass(frozen=True, slots=True)
class PlainPassword:
    """Validated plain-text password before hashing."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < _MIN_LENGTH:
            raise WeakPasswordError(f"Password must be at least {_MIN_LENGTH} characters")
        if len(self.value) > _MAX_LENGTH:
            raise WeakPasswordError(f"Password must be at most {_MAX_LENGTH} characters")
        if not _LETTER_PATTERN.search(self.value) or not _DIGIT_PATTERN.search(self.value):
            raise WeakPasswordError("Password must contain at least one letter and one digit")
