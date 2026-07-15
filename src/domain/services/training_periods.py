"""Date range helpers for training plan and report queries."""

import calendar
from datetime import UTC, date, datetime, time, timedelta

PLAN_PERIOD_WEEK = "week"
PLAN_PERIOD_MONTH = "month"
REPORT_PERIOD_WEEK = "week"
REPORT_PERIOD_MONTH = "month"


def resolve_anchor_date(anchor_date: date | None, *, today: date | None = None) -> date:
    """Return anchor_date or today in UTC."""
    if anchor_date is not None:
        return anchor_date
    return today or datetime.now(UTC).date()


def start_of_week(anchor_date: date) -> date:
    """Return Monday of the calendar week containing anchor_date."""
    return anchor_date - timedelta(days=anchor_date.weekday())


def plan_week_range(anchor_date: date) -> tuple[date, date]:
    """Return inclusive Monday–Sunday plan dates for the week containing anchor_date."""
    week_start = start_of_week(anchor_date)
    return week_start, week_start + timedelta(days=6)


def plan_month_range(anchor_date: date) -> tuple[date, date]:
    """Return inclusive plan dates for the calendar month containing anchor_date."""
    last_day = calendar.monthrange(anchor_date.year, anchor_date.month)[1]
    return anchor_date.replace(day=1), anchor_date.replace(day=last_day)


def report_week_range(anchor_date: date) -> tuple[datetime, datetime]:
    """Return UTC datetimes for seven days ending on anchor_date."""
    start_date = anchor_date - timedelta(days=6)
    return _day_start(start_date), _day_end(anchor_date)


def report_month_range(anchor_date: date) -> tuple[datetime, datetime]:
    """Return UTC datetimes for thirty days ending on anchor_date."""
    start_date = anchor_date - timedelta(days=29)
    return _day_start(start_date), _day_end(anchor_date)


def _day_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _day_end(value: date) -> datetime:
    return datetime.combine(value, time(23, 59, 59), tzinfo=UTC)
