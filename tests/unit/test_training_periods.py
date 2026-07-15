"""Unit tests for training period calculations."""

from datetime import UTC, date, datetime

from domain.services.training_periods import (
    plan_month_range,
    plan_week_range,
    report_month_range,
    report_week_range,
    resolve_anchor_date,
)


def test_resolve_anchor_date_uses_provided_date() -> None:
    anchor = date(2026, 7, 15)
    assert resolve_anchor_date(anchor, today=date(2026, 1, 1)) == anchor


def test_resolve_anchor_date_defaults_to_today() -> None:
    today = date(2026, 6, 26)
    assert resolve_anchor_date(None, today=today) == today


def test_plan_week_range_returns_monday_to_sunday_week() -> None:
    anchor = date(2026, 7, 15)  # Wednesday
    start_date, end_date = plan_week_range(anchor)
    assert start_date == date(2026, 7, 13)  # Monday
    assert end_date == date(2026, 7, 19)  # Sunday


def test_plan_week_range_when_anchor_is_sunday() -> None:
    anchor = date(2026, 7, 19)  # Sunday
    start_date, end_date = plan_week_range(anchor)
    assert start_date == date(2026, 7, 13)
    assert end_date == date(2026, 7, 19)


def test_plan_month_range_returns_calendar_month() -> None:
    anchor = date(2026, 7, 15)
    start_date, end_date = plan_month_range(anchor)
    assert start_date == date(2026, 7, 1)
    assert end_date == date(2026, 7, 31)


def test_report_week_range_returns_seven_days_backward() -> None:
    anchor = date(2026, 7, 10)
    start_at, end_at = report_week_range(anchor)
    assert start_at == datetime(2026, 7, 4, 0, 0, tzinfo=UTC)
    assert end_at == datetime(2026, 7, 10, 23, 59, 59, tzinfo=UTC)


def test_report_month_range_returns_thirty_days_backward() -> None:
    anchor = date(2026, 7, 10)
    start_at, end_at = report_month_range(anchor)
    assert start_at == datetime(2026, 6, 11, 0, 0, tzinfo=UTC)
    assert end_at == datetime(2026, 7, 10, 23, 59, 59, tzinfo=UTC)
