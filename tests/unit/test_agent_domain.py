"""Unit tests for agent domain rules and prompts."""

from domain.services.agent_session_rules import (
    AGENT_SESSION_EXPIRY_HOURS,
    AI_CALL_TIMEOUT_SECONDS,
    MAX_AGENT_MESSAGES_PER_SESSION,
)
from infrastructure.ai.prompt_loader import load_prompt_template, render_prompt_template


def test_agent_session_limits_are_documented() -> None:
    assert MAX_AGENT_MESSAGES_PER_SESSION == 20
    assert AI_CALL_TIMEOUT_SECONDS == 30
    assert AGENT_SESSION_EXPIRY_HOURS == 24


def test_coach_plan_prompt_loads() -> None:
    content = load_prompt_template("coach_plan_system.md")
    assert "plan_draft" in content
    assert "question" in content


def test_athlete_report_prompt_renders_context() -> None:
    rendered = render_prompt_template(
        "athlete_report_system.md",
        workout_context="Run 8 km easy",
    )
    assert "Run 8 km easy" in rendered
    assert "report_draft" in rendered
