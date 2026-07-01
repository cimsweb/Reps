"""Tests for SubmitWorkoutFeedbackUseCase."""

from uuid import uuid4

import pytest

from application.use_cases.submit_workout_feedback import SubmitWorkoutFeedbackUseCase
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, InvalidFeedbackTextError, InvalidGarminUrlError
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryWorkoutFeedbackRepository


def test_submit_workout_feedback_without_garmin_url() -> None:
    repository = InMemoryWorkoutFeedbackRepository()
    athlete_id = UserId(uuid4())
    use_case = SubmitWorkoutFeedbackUseCase(repository)

    feedback = use_case.execute(athlete_id, Role.ATHLETE, "Felt strong today")

    assert feedback.text == "Felt strong today"
    assert feedback.garmin_url is None


def test_submit_workout_feedback_with_garmin_url() -> None:
    repository = InMemoryWorkoutFeedbackRepository()
    athlete_id = UserId(uuid4())
    garmin_url = "https://connect.garmin.com/modern/activity/12345"

    feedback = SubmitWorkoutFeedbackUseCase(repository).execute(
        athlete_id,
        Role.ATHLETE,
        "Hard intervals",
        garmin_url,
    )

    assert feedback.garmin_url is not None
    assert str(feedback.garmin_url) == garmin_url


def test_submit_workout_feedback_rejects_invalid_garmin_url() -> None:
    with pytest.raises(InvalidGarminUrlError):
        SubmitWorkoutFeedbackUseCase(InMemoryWorkoutFeedbackRepository()).execute(
            UserId(uuid4()),
            Role.ATHLETE,
            "Feedback",
            "https://example.com/report",
        )


def test_submit_workout_feedback_rejects_empty_text() -> None:
    with pytest.raises(InvalidFeedbackTextError):
        SubmitWorkoutFeedbackUseCase(InMemoryWorkoutFeedbackRepository()).execute(
            UserId(uuid4()),
            Role.ATHLETE,
            "   ",
        )


def test_submit_workout_feedback_rejects_coach_role() -> None:
    with pytest.raises(AuthorizationError):
        SubmitWorkoutFeedbackUseCase(InMemoryWorkoutFeedbackRepository()).execute(
            UserId(uuid4()),
            Role.COACH,
            "Feedback",
        )
