"""Tests for SubmitWorkoutFeedbackUseCase."""

from uuid import uuid4

import pytest

from application.use_cases.submit_workout_feedback import SubmitWorkoutFeedbackUseCase
from domain.entities.role import Role
from domain.exceptions import AuthorizationError, InvalidFeedbackTextError
from domain.value_objects.user_id import UserId
from fakes.in_memory_coaching_repositories import InMemoryWorkoutFeedbackRepository


def test_submit_workout_feedback_saves_text() -> None:
    repository = InMemoryWorkoutFeedbackRepository()
    athlete_id = UserId(uuid4())
    use_case = SubmitWorkoutFeedbackUseCase(repository)

    feedback = use_case.execute(athlete_id, Role.ATHLETE, "Felt strong today")

    assert feedback.text == "Felt strong today"


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
