from enum import StrEnum


class PlanScope(StrEnum):
    """Training plan period length."""

    DAY = "day"
    WEEK = "week"
