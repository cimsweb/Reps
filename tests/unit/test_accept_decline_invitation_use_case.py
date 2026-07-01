"""Tests for AcceptInvitationUseCase and DeclineInvitationUseCase."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from application.use_cases.accept_invitation import AcceptInvitationUseCase
from application.use_cases.decline_invitation import DeclineInvitationUseCase
from application.use_cases.send_invitation import SendInvitationUseCase
from domain.entities.invitation_status import InvitationStatus
from domain.entities.role import Role
from domain.entities.user import User
from domain.exceptions import (
    InvitationAlreadyRespondedError,
    InvitationEmailMismatchError,
    InvitationNotFoundError,
)
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


def test_accept_invitation_creates_link() -> None:
    users = InMemoryUserRepository()
    invitations = InMemoryInvitationRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)

    invitation = SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "athlete@example.com",
    )

    link = AcceptInvitationUseCase(invitations, links).execute(
        athlete.id,
        Role.ATHLETE,
        "athlete@example.com",
        str(invitation.id),
    )

    assert link.coach_id == coach.id
    assert link.athlete_id == athlete.id
    updated = invitations.get_by_id(invitation.id)
    assert updated is not None
    assert updated.status is InvitationStatus.ACCEPTED


def test_accept_invitation_rejects_wrong_email() -> None:
    users = InMemoryUserRepository()
    invitations = InMemoryInvitationRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)
    invitation = SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "athlete@example.com",
    )

    with pytest.raises(InvitationEmailMismatchError):
        AcceptInvitationUseCase(invitations, links).execute(
            athlete.id,
            Role.ATHLETE,
            "wrong@example.com",
            str(invitation.id),
        )


def test_accept_invitation_rejects_missing_invitation() -> None:
    athlete_id = UserId(uuid4())
    with pytest.raises(InvitationNotFoundError):
        AcceptInvitationUseCase(
            InMemoryInvitationRepository(),
            InMemoryCoachAthleteLinkRepository(),
        ).execute(
            athlete_id,
            Role.ATHLETE,
            "athlete@example.com",
            str(uuid4()),
        )


def test_decline_invitation_updates_status() -> None:
    users = InMemoryUserRepository()
    invitations = InMemoryInvitationRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)
    invitation = SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "athlete@example.com",
    )

    declined = DeclineInvitationUseCase(invitations).execute(
        athlete.id,
        Role.ATHLETE,
        "athlete@example.com",
        str(invitation.id),
    )

    assert declined.status is InvitationStatus.DECLINED
    assert declined.responded_at is not None


def test_decline_invitation_rejects_already_responded() -> None:
    users = InMemoryUserRepository()
    invitations = InMemoryInvitationRepository()
    links = InMemoryCoachAthleteLinkRepository()
    coach = _save_user(users, "coach@example.com", Role.COACH)
    athlete = _save_user(users, "athlete@example.com", Role.ATHLETE)
    invitation = SendInvitationUseCase(invitations, links, users).execute(
        coach.id,
        Role.COACH,
        "athlete@example.com",
    )
    AcceptInvitationUseCase(invitations, links).execute(
        athlete.id,
        Role.ATHLETE,
        "athlete@example.com",
        str(invitation.id),
    )

    with pytest.raises(InvitationAlreadyRespondedError):
        DeclineInvitationUseCase(invitations).execute(
            athlete.id,
            Role.ATHLETE,
            "athlete@example.com",
            str(invitation.id),
        )
