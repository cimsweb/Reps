from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from domain.entities.workout_type import WorkoutType
from domain.value_objects.garmin_report_url import GarminReportUrl


@dataclass(frozen=True, slots=True)
class ParsedWorkoutDraft:
    """A parsed planned workout draft without identifiers."""

    planned_date: date
    workout_type: WorkoutType
    title: str | None
    cycles: tuple[ParsedCycleDraft, ...]


@dataclass(frozen=True, slots=True)
class ParsedCycleDraft:
    """A parsed workout cycle draft without identifiers."""

    name: str
    sort_order: int
    exercises: tuple[ParsedExerciseDraft, ...]


@dataclass(frozen=True, slots=True)
class ParsedExerciseDraft:
    """A parsed workout exercise draft without identifiers."""

    name: str
    details: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class ParsedTrainingDraft:
    """Result of parsing training plan text into structured draft workouts."""

    workouts: tuple[ParsedWorkoutDraft, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportDraft:
    """Result of parsing athlete report free text into suggested structured fields."""

    garmin_url: GarminReportUrl | None = None
    suggested_difficulty_rating: int | None = None
    suggested_mood_rating: int | None = None
    comment_body: str | None = None
    warnings: tuple[str, ...] = ()


class TrainingTextParser(Protocol):
    def parse_day(self, *, text: str, planned_date: date) -> ParsedTrainingDraft: ...

    def parse_week(self, *, text: str, start_date: date) -> ParsedTrainingDraft: ...


class ReportTextParser(Protocol):
    def parse_report_text(self, *, text: str) -> ReportDraft: ...
