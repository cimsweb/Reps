import logging
from datetime import UTC, datetime

from domain.entities.athlete_profile import AthleteProfile
from domain.entities.gender import Gender
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, DomainError, InvalidProfileDataError
from domain.repositories.athlete_profile_repository import AthleteProfileRepository
from domain.value_objects.age import Age
from domain.value_objects.height_cm import HeightCm
from domain.value_objects.user_id import UserId
from domain.value_objects.weight_kg import WeightKg
from infrastructure.logging.setup import log_coaching_event


class SaveAthleteProfileUseCase:
    """Athlete creates or updates their profile."""

    def __init__(
        self,
        profile_repository: AthleteProfileRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._profile_repository = profile_repository
        self._logger = logger or logging.getLogger("reps.coaching")

    def execute(
        self,
        athlete_id: UserId,
        athlete_role: Role,
        height_cm: int,
        weight_kg: int,
        age: int,
        gender: str,
    ) -> AthleteProfile:
        """Save athlete profile with validated fields."""
        try:
            if athlete_role is not Role.ATHLETE:
                raise AuthorizationError("Only athletes can edit their profile")

            try:
                parsed_gender = Gender(gender)
            except ValueError as error:
                raise InvalidProfileDataError(f"Unknown gender: {gender}") from error

            profile = AthleteProfile(
                athlete_id=athlete_id,
                height_cm=HeightCm(height_cm),
                weight_kg=WeightKg(weight_kg),
                age=Age(age),
                gender=parsed_gender,
                updated_at=datetime.now(UTC),
            )
            saved_profile = self._profile_repository.save(profile)
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
            "athlete_profile_saved",
            success=True,
            user_id=str(athlete_id),
            message="Athlete profile saved",
        )
        return saved_profile
