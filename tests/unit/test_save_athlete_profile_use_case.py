"""Tests for SaveAthleteProfileUseCase."""

from uuid import uuid4

import pytest

from application.use_cases.save_athlete_profile import SaveAthleteProfileUseCase
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, InvalidProfileDataError
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryAthleteProfileRepository


def test_save_athlete_profile_creates_profile() -> None:
    repository = InMemoryAthleteProfileRepository()
    athlete_id = UserId(uuid4())
    use_case = SaveAthleteProfileUseCase(repository)

    profile = use_case.execute(athlete_id, Role.ATHLETE, 180, 75, 28, "male")

    assert profile.height_cm.value == 180
    assert profile.gender.value == "male"


def test_save_athlete_profile_updates_existing_profile() -> None:
    repository = InMemoryAthleteProfileRepository()
    athlete_id = UserId(uuid4())
    use_case = SaveAthleteProfileUseCase(repository)
    use_case.execute(athlete_id, Role.ATHLETE, 180, 75, 28, "male")

    updated = use_case.execute(athlete_id, Role.ATHLETE, 181, 76, 29, "male")

    assert updated.height_cm.value == 181
    assert updated.age.value == 29


def test_save_athlete_profile_rejects_invalid_height() -> None:
    use_case = SaveAthleteProfileUseCase(InMemoryAthleteProfileRepository())

    with pytest.raises(InvalidProfileDataError):
        use_case.execute(UserId(uuid4()), Role.ATHLETE, 50, 75, 28, "male")


def test_save_athlete_profile_rejects_non_athlete() -> None:
    use_case = SaveAthleteProfileUseCase(InMemoryAthleteProfileRepository())

    with pytest.raises(AuthorizationError):
        use_case.execute(UserId(uuid4()), Role.COACH, 180, 75, 28, "male")
