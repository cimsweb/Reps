from enum import StrEnum


class AgentSessionKind(StrEnum):
    """Type of AI-assisted dialog session."""

    PLAN_CREATION = "plan_creation"
    REPORT_ASSISTANCE = "report_assistance"
