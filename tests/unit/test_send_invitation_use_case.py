"""Tests for SendInvitationUseCase."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.use_cases.send_invitation import SendInvitationUseCase
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import (
    AuthorizationError,
    CoachAthleteLinkAlreadyExistsError,
    DuplicateInvitationError,
    InvalidInvitationTargetError,
)
from domain.value_objects.coach_athlete_link_id import CoachAthleteLinkId
from domain.value_objects.email import Email
from domain.value_objects.password_hash import PasswordHash
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import (
    InMemoryCoachAthleteLinkRepository,
    InMemoryInvitationRepository,
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


def test_send_invitation_creates_pending_invitation() -> None:
    users = InMemoryUserRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    use_case = SendInvitationUseCase(
        InMemoryInvitationRepository(),
        InMemoryCoachAthleteLinkRepository(),
        users,
    )

    invitation = use_case.execute(coach.id, Role.COACH, "athlete@example.com")

    assert invitation.status.value == "pending"
    assert str(invitation.athlete_email) == "athlete@example.com"


def test_send_invitation_rejects_non_coach_role() -> None:
    users = InMemoryUserRepository()
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)
    use_case = SendInvitationUseCase(
        InMemoryInvitationRepository(),
        InMemoryCoachAthleteLinkRepository(),
        users,
    )

    with pytest.raises(AuthorizationError):
        use_case.execute(athlete.id, Role.ATHLETE, "other@example.com")


def test_send_invitation_rejects_duplicate_pending() -> None:
    users = InMemoryUserRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    use_case = SendInvitationUseCase(
        InMemoryInvitationRepository(),
        InMemoryCoachAthleteLinkRepository(),
        users,
    )
    use_case.execute(coach.id, Role.COACH, "athlete@example.com")

    with pytest.raises(DuplicateInvitationError):
        use_case.execute(coach.id, Role.COACH, "athlete@example.com")


def test_send_invitation_rejects_existing_link() -> None:
    users = InMemoryUserRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)
    links = InMemoryCoachAthleteLinkRepository()
    links.save(
        CoachAthleteLink(
            id=CoachAthleteLinkId(uuid4()),
            coach_id=coach.id,
            athlete_id=athlete.id,
            created_at=datetime.now(UTC),
        )
    )
    use_case = SendInvitationUseCase(InMemoryInvitationRepository(), links, users)

    with pytest.raises(CoachAthleteLinkAlreadyExistsError):
        use_case.execute(coach.id, Role.COACH, "athlete@example.com")


def test_send_invitation_rejects_self_invite() -> None:
    users = InMemoryUserRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    use_case = SendInvitationUseCase(
        InMemoryInvitationRepository(),
        InMemoryCoachAthleteLinkRepository(),
        users,
    )

    with pytest.raises(InvalidInvitationTargetError):
        use_case.execute(coach.id, Role.COACH, "coach@example.com")


def test_send_invitation_rejects_non_athlete_target() -> None:
    users = InMemoryUserRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    _save_user(users, "other-coach@example.com", Role.COACH)
    use_case = SendInvitationUseCase(
        InMemoryInvitationRepository(),
        InMemoryCoachAthleteLinkRepository(),
        users,
    )

    with pytest.raises(InvalidInvitationTargetError):
        use_case.execute(coach.id, Role.COACH, "other-coach@example.com")
