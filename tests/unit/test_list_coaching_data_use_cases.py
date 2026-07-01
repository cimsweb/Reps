"""Tests for MVP 1 read use cases."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.security.coaching_access_guard import CoachingAccessGuard
from application.use_cases.decline_invitation import DeclineInvitationUseCase
from application.use_cases.list_coaching_data import (
    GetAthleteProfileUseCase,
    ListAthleteCoachesUseCase,
    ListCoachAthletesUseCase,
    ListCoachInvitationsUseCase,
    ListPendingInvitationsUseCase,
    ListPersonalRecordsUseCase,
    ListWorkoutFeedbackUseCase,
)
from application.use_cases.send_invitation import SendInvitationUseCase
from domain.entities.athlete_profile import AthleteProfile
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.gender import Gender
from domain.entities.invitation_status import InvitationStatus
from domain.entities.role import Role
from domain.entities.user import User
from domain.entities.workout_feedback import WorkoutFeedback
from domain.exceptions import (
    AthleteDataAccessDeniedError,
    AthleteProfileNotFoundError,
    AuthorizationError,
    CoachAthleteAccessDeniedError,
)
from domain.value_objects.age import Age
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.email import Email
from domain.value_objects.feedback_text import FeedbackText
from domain.value_objects.height_cm import HeightCm
from domain.value_objects.pagination import PageRequest
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId
from domain.value_objects.weight_kg import WeightKg
from domain.value_objects.workout_feedback_id import WorkoutFeedbackId
from fakes.in_memory_coaching_repositories import (
    InMemoryAthleteProfileRepository,
    InMemoryCoachAthleteLinkRepository,
    InMemoryInvitationRepository,
    InMemoryPersonalRecordRepository,
    InMemoryWorkoutFeedbackRepository,
)
from fakes.in_memory_repositories import InMemoryUserRepository


def _save_user(
    repository: InMemoryUserRepository,
    email: str,
    role: Role,
) -> User:
    user = User(
        id=UserId(uuid4()),
        email=Email(email),
        password_hash=PasswordHash("hash"),
        role=role,
        created_at=datetime.now(UTC),
    )
    return repository.save(user)


def _save_profile(repository: InMemoryAthleteProfileRepository, athlete_id: UserId) -> None:
    repository.save(
        AthleteProfile(
            athlete_id=athlete_id,
            height_cm=HeightCm(180),
            weight_kg=WeightKg(75),
            age=Age(28),
            gender=Gender.MALE,
            updated_at=datetime.now(UTC),
        )
    )


def _link_coach_and_athlete(
    links: InMemoryCoachAthleteLinkRepository,
    coach_id: UserId,
    athlete_id: UserId,
) -> CoachAthleteLink:
    link = CoachAthleteLink(
        id=CoachAthleteLinkId(uuid4()),
        coach_id=coach_id,
        athlete_id=athlete_id,
        created_at=datetime.now(UTC),
    )
    return links.save(link)


def test_list_coach_invitations_returns_all_statuses() -> None:
    users = InMemoryUserRepository()
    invitations = InMemoryInvitationRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    pending_athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)
    declining_athlete = _save_user(users, "other@example.com", Role.ATHLETE)

    SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "athlete@example.com",
    )
    declined_invitation = SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "other@example.com",
    )
    DeclineInvitationUseCase(invitations).execute(
        declining_athlete.id,
        Role.ATHLETE,
        "other@example.com",
        str(declined_invitation.id.value),
    )

    result = ListCoachInvitationsUseCase(invitations).execute(coach.id, Role.COACH)
    statuses = {item.status for item in result}
    assert len(result) == 2
    assert InvitationStatus.PENDING.value in statuses
    assert InvitationStatus.DECLINED.value in statuses
    _ = pending_athlete


def test_list_coach_invitations_rejects_athlete() -> None:
    athlete_id = UserId(uuid4())
    with pytest.raises(AuthorizationError):
        ListCoachInvitationsUseCase(InMemoryInvitationRepository()).execute(
            athlete_id,
            Role.ATHLETE,
        )


def test_list_pending_invitations_for_athlete_email() -> None:
    users = InMemoryUserRepository()
    invitations = InMemoryInvitationRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)

    SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "athlete@example.com",
    )

    result = ListPendingInvitationsUseCase(invitations).execute(
        athlete.id,
        Role.ATHLETE,
        "athlete@example.com",
    )
    assert len(result) == 1
    assert result[0].status == InvitationStatus.PENDING.value


def test_list_coach_athletes_returns_links() -> None:
    links = InMemoryCoachAthleteLinkRepository()
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    _link_coach_and_athlete(links, coach_id, athlete_id)

    result = ListCoachAthletesUseCase(links).execute(coach_id, Role.COACH)
    assert len(result) == 1
    assert result[0].athlete_id == str(athlete_id.value)


def test_list_athlete_coaches_returns_links() -> None:
    links = InMemoryCoachAthleteLinkRepository()
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    _link_coach_and_athlete(links, coach_id, athlete_id)

    result = ListAthleteCoachesUseCase(links).execute(athlete_id, Role.ATHLETE)
    assert len(result) == 1
    assert result[0].coach_id == str(coach_id.value)


def test_get_athlete_profile_for_self() -> None:
    profiles = InMemoryAthleteProfileRepository()
    links = InMemoryCoachAthleteLinkRepository()
    athlete_id = UserId(uuid4())
    _save_profile(profiles, athlete_id)

    result = GetAthleteProfileUseCase(
        profiles,
        CoachingAccessGuard(links),
    ).execute(athlete_id, Role.ATHLETE, athlete_id)

    assert result.athlete_id == str(athlete_id.value)
    assert result.height_cm == 180


def test_get_athlete_profile_for_linked_coach() -> None:
    profiles = InMemoryAthleteProfileRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    _save_profile(profiles, athlete_id)
    _link_coach_and_athlete(links, coach_id, athlete_id)

    result = GetAthleteProfileUseCase(
        profiles,
        CoachingAccessGuard(links),
    ).execute(coach_id, Role.COACH, athlete_id)

    assert result.age == 28


def test_get_athlete_profile_not_found() -> None:
    athlete_id = UserId(uuid4())
    with pytest.raises(AthleteProfileNotFoundError):
        GetAthleteProfileUseCase(
            InMemoryAthleteProfileRepository(),
            CoachingAccessGuard(InMemoryCoachAthleteLinkRepository()),
        ).execute(athlete_id, Role.ATHLETE, athlete_id)


def test_get_athlete_profile_denies_unlinked_coach() -> None:
    profiles = InMemoryAthleteProfileRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    _save_profile(profiles, athlete_id)

    with pytest.raises(CoachAthleteAccessDeniedError):
        GetAthleteProfileUseCase(
            profiles,
            CoachingAccessGuard(links),
        ).execute(coach_id, Role.COACH, athlete_id)


def test_get_athlete_profile_denies_other_athlete() -> None:
    profiles = InMemoryAthleteProfileRepository()
    links = InMemoryCoachAthleteLinkRepository()
    athlete_id = UserId(uuid4())
    other_athlete_id = UserId(uuid4())
    _save_profile(profiles, other_athlete_id)

    with pytest.raises(AthleteDataAccessDeniedError):
        GetAthleteProfileUseCase(
            profiles,
            CoachingAccessGuard(links),
        ).execute(athlete_id, Role.ATHLETE, other_athlete_id)


def test_list_personal_records_with_pagination() -> None:
    from application.use_cases.personal_record_commands import CreatePersonalRecordUseCase

    records = InMemoryPersonalRecordRepository()
    links = InMemoryCoachAthleteLinkRepository()
    athlete_id = UserId(uuid4())

    for index in range(3):
        CreatePersonalRecordUseCase(records).execute(
            athlete_id,
            Role.ATHLETE,
            "distance",
            f"{index + 1}K",
            f"0{index}:00",
            "time",
            datetime.now(UTC),
        )

    result = ListPersonalRecordsUseCase(
        records,
        CoachingAccessGuard(links),
    ).execute(
        athlete_id,
        Role.ATHLETE,
        athlete_id,
        PageRequest(offset=1, limit=1),
    )

    assert result.total == 3
    assert len(result.items) == 1


def test_list_workout_feedback_for_linked_coach() -> None:
    feedback_repository = InMemoryWorkoutFeedbackRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach_id = UserId(uuid4())
    athlete_id = UserId(uuid4())
    _link_coach_and_athlete(links, coach_id, athlete_id)
    feedback_repository.save(
        WorkoutFeedback(
            id=WorkoutFeedbackId(uuid4()),
            athlete_id=athlete_id,
            text=FeedbackText("Good session").value,
            garmin_url=None,
            created_at=datetime.now(UTC),
        )
    )

    result = ListWorkoutFeedbackUseCase(
        feedback_repository,
        CoachingAccessGuard(links),
    ).execute(coach_id, Role.COACH, athlete_id)

    assert result.total == 1
    assert result.items[0].text == "Good session"
