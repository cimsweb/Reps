from dataclasses import dataclass

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Pagination parameters for list queries."""

    offset: int = 0
    limit: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValueError("Page offset cannot be negative")
        if self.limit < 1:
            raise ValueError("Page limit must be at least 1")
        if self.limit > MAX_PAGE_SIZE:
            raise ValueError(f"Page limit cannot exceed {MAX_PAGE_SIZE}")
