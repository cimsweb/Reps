"""Unit tests for MVP 1 value objects."""

import pytest

from domain.exceptions import InvalidGarminUrlError, InvalidProfileDataError
from domain.value_objects.age import Age
from domain.value_objects.feedback_text import FeedbackText
from domain.value_objects.garmin_report_url import GarminReportUrl
from domain.value_objects.height_cm import HeightCm
from domain.value_objects.record_name import RecordName
from domain.value_objects.weight_kg import WeightKg


def test_height_cm_accepts_valid_value() -> None:
    height = HeightCm(180)
    assert height.value == 180


@pytest.mark.parametrize("value", [99, 251])
def test_height_cm_rejects_out_of_range(value: int) -> None:
    with pytest.raises(InvalidProfileDataError):
        HeightCm(value)


def test_age_accepts_valid_value() -> None:
    age = Age(25)
    assert age.value == 25


def test_garmin_report_url_accepts_valid_https_url() -> None:
    url = GarminReportUrl("https://connect.garmin.com/modern/activity/123")
    assert "garmin.com" in url.value


def test_garmin_report_url_accepts_strava_url() -> None:
    url = GarminReportUrl("https://www.strava.com/activities/12345")
    assert "strava.com" in url.value


def test_garmin_report_url_rejects_non_https() -> None:
    with pytest.raises(InvalidGarminUrlError):
        GarminReportUrl("http://www.strava.com/activities/1")


def test_weight_kg_accepts_valid_value() -> None:
    weight = WeightKg(75)
    assert weight.value == 75


def test_feedback_text_accepts_non_empty_value() -> None:
    text = FeedbackText("Good workout")
    assert text.value == "Good workout"


def test_record_name_accepts_non_empty_value() -> None:
    name = RecordName("5K")
    assert name.value == "5K"
