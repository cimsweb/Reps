"""Shared pytest fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def enable_ai_stub_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep AI agent tests deterministic unless AI_API_KEY is explicitly set."""
    if not os.getenv("AI_API_KEY"):
        monkeypatch.setenv("AI_USE_STUB", "true")
