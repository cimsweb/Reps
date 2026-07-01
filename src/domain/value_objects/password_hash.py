from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Stored password hash. Plain passwords never enter this type."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Password hash cannot be empty")

    def __str__(self) -> str:
        return self.value
