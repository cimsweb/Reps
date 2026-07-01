from typing import Protocol

from domain.entities.personal_record import PersonalRecord
from domain.entities.record_type import RecordType
from domain.value_objects.personal_record_id import PersonalRecordId
from domain.value_objects.user_id import UserId


class PersonalRecordRepository(Protocol):
    """Persistence contract for personal records."""

    def save(self, record: PersonalRecord) -> PersonalRecord:
        """Persist a personal record."""

    def get_by_id(self, record_id: PersonalRecordId) -> PersonalRecord | None:
        """Load personal record by identifier."""

    def delete(self, record_id: PersonalRecordId) -> None:
        """Delete a personal record."""

    def list_by_athlete(self, athlete_id: UserId) -> list[PersonalRecord]:
        """Return all records for an athlete."""

    def list_by_athlete_and_type(
        self,
        athlete_id: UserId,
        record_type: RecordType,
    ) -> list[PersonalRecord]:
        """Return athlete records filtered by type."""

    def list_by_athlete_page(
        self,
        athlete_id: UserId,
        *,
        offset: int,
        limit: int,
    ) -> list[PersonalRecord]:
        """Return a page of personal records for an athlete."""

    def count_by_athlete(self, athlete_id: UserId) -> int:
        """Return total number of personal records for an athlete."""
