from dataclasses import dataclass
from urllib.parse import urlparse

from domain.exceptions import InvalidGarminUrlError

_MAX_URL_LENGTH = 2048


@dataclass(frozen=True, slots=True)
class GarminReportUrl:
    """Validated Garmin Connect report URL."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidGarminUrlError("Garmin report URL cannot be empty")
        if len(normalized) > _MAX_URL_LENGTH:
            raise InvalidGarminUrlError(
                f"Garmin report URL must be at most {_MAX_URL_LENGTH} characters"
            )

        parsed = urlparse(normalized)
        if parsed.scheme != "https" or not parsed.netloc:
            raise InvalidGarminUrlError("Garmin report URL must be a valid HTTPS URL")
        if "garmin.com" not in parsed.netloc:
            raise InvalidGarminUrlError("Garmin report URL must point to garmin.com")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
