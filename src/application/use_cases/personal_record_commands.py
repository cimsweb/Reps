import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.entities.personal_record import PersonalRecord
from domain.entities.record_type import RecordType
from domain.entities.role import Role
from domain.exceptions import (
    AuthorizationError,
    DomainError,
    InvalidPersonalRecordError,
    PersonalRecordNotFoundError,
    RecordOwnershipError,
)
from domain.repositories.personal_record_repository import PersonalRecordRepository
from domain.value_objects.personal_record_id import PersonalRecordId
from domain.value_objects.record_name import RecordName
from domain.value_objects.record_unit import RecordUnit
from domain.value_objects.record_value import RecordValue
from domain.value_objects.user_id import UserId
from infrastructure.logging.setup import log_coaching_event


class CreatePersonalRecordUseCase:
    """Athlete adds a personal record."""

    def __init__(
        self,
        record_repository: PersonalRecordRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._record_repository = record_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        record_type: str,
        name: str,
        value: str,
        unit: str,
        achieved_at: datetime,
    ) -> PersonalRecord:
        """Create a personal record for the athlete."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can create personal records")

            try:
                parsed_record_type = RecordType(record_type)
            except ValueError as error:
                raise InvalidPersonalRecordError(f"Unknown record type: {record_type}") from error

            now = datetime.now(UTC)
            record = PersonalRecord(
                id=PersonalRecordId(uuid4()),
                athlete_id=athlete_id,
                record_type=parsed_record_type,
                name=RecordName(name).value,
                value=RecordValue(value),
                unit=RecordUnit(unit),
                achieved_at=achieved_at,
                created_at=now,
            )
            saved_record = self._record_repository.save(record)
        except DomainError as error:
            log_coaching_event(
                self._logger,
                "coaching_validation_error",
                success=False,
                user_id=str(athlete_id),
                message=str(error),
            )
            raise

        log_coaching_event(
            self._logger,
            "personal_record_saved",
            success=True,
            user_id=str(athlete_id),
            message=f"Personal record created: {name}",
        )
        return saved_record


class UpdatePersonalRecordUseCase:
    """Athlete updates an existing personal record."""

    def __init__(
        self,
        record_repository: PersonalRecordRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._record_repository = record_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        record_id: str,
        record_type: str,
        name: str,
        value: str,
        unit: str,
        achieved_at: datetime,
    ) -> PersonalRecord:
        """Update a personal record owned by the athlete."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can update personal records")

            existing_record = self._record_repository.get_by_id(PersonalRecordId(UUID(record_id)))
            if existing_record is None:
                raise PersonalRecordNotFoundError(f"Personal record not found: {record_id}")
            if existing_record.athlete_id != athlete_id:
                raise RecordOwnershipError("Athlete can only update their own records")

            try:
                parsed_record_type = RecordType(record_type)
            except ValueError as error:
                raise InvalidPersonalRecordError(f"Unknown record type: {record_type}") from error

            updated_record = PersonalRecord(
                id=existing_record.id,
                athlete_id=existing_record.athlete_id,
                record_type=parsed_record_type,
                name=RecordName(name).value,
                value=RecordValue(value),
                unit=RecordUnit(unit),
                achieved_at=achieved_at,
                created_at=existing_record.created_at,
            )
            saved_record = self._record_repository.save(updated_record)
        except DomainError as error:
            log_coaching_event(
                self._logger,
                "coaching_validation_error",
                success=False,
                user_id=str(athlete_id),
                message=str(error),
            )
            raise

        log_coaching_event(
            self._logger,
            "personal_record_saved",
            success=True,
            user_id=str(athlete_id),
            message=f"Personal record updated: {record_id}",
        )
        return saved_record


class DeletePersonalRecordUseCase:
    """Athlete deletes a personal record."""

    def __init__(
        self,
        record_repository: PersonalRecordRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._record_repository = record_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(self, athlete_id: UserId, athlete_role: Role, record_id: str) -> None:
        """Delete a personal record owned by the athlete."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can delete personal records")

            parsed_record_id = PersonalRecordId(UUID(record_id))
            existing_record = self._record_repository.get_by_id(parsed_record_id)
            if existing_record is None:
                raise PersonalRecordNotFoundError(f"Personal record not found: {record_id}")
            if existing_record.athlete_id != athlete_id:
                raise RecordOwnershipError("Athlete can only delete their own records")

            self._record_repository.delete(parsed_record_id)
        except DomainError as error:
            log_coaching_event(
                self._logger,
                "coaching_validation_error",
                success=False,
                user_id=str(athlete_id),
                message=str(error),
            )
            raise

        log_coaching_event(
            self._logger,
            "personal_record_deleted",
            success=True,
            user_id=str(athlete_id),
            message=f"Personal record deleted: {record_id}",
        )
