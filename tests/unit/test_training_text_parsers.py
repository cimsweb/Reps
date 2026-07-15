from __future__ import annotations

from datetime import date
from pathlib import Path

from domain.entities.workout_type import WorkoutType
from infrastructure.parsing.rule_based_report_text_parser import RuleBasedReportTextParser
from infrastructure.parsing.rule_based_training_text_parser import RuleBasedTrainingTextParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "training_text"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_week_tsv_fixture_parses_into_seven_workouts() -> None:
    parser = RuleBasedTrainingTextParser()
    text = _read_fixture("week_2024-06-08.tsv")
    draft = parser.parse_week(text=text, start_date=date(2024, 6, 8))

    assert len(draft.workouts) == 7
    assert draft.workouts[0].planned_date == date(2024, 6, 8)
    assert draft.workouts[-1].planned_date == date(2024, 6, 14)

    # Sanity: at least one day inferred as bike, and at least one as gym.
    workout_types = {workout.workout_type for workout in draft.workouts}
    assert WorkoutType.BIKE in workout_types
    assert WorkoutType.GYM in workout_types


def test_week_day_headers_parse_into_multiple_workouts() -> None:
    parser = RuleBasedTrainingTextParser()
    blocks = [
        "7 Июля\n\nСуставная разминка\n\n20 мин бега",
        "8 Июля\n\nВелостанок\n\n60 мин",
        "9 Июля\n\nСуставная разминка\n\n15 мин бега",
    ]
    text = "\n\n".join(blocks)
    draft = parser.parse_week(text=text, start_date=date(2024, 7, 7))

    assert len(draft.workouts) == 3
    assert draft.workouts[0].planned_date == date(2024, 7, 7)
    assert draft.workouts[1].planned_date == date(2024, 7, 8)
    assert draft.workouts[2].planned_date == date(2024, 7, 9)


def test_week_parser_skips_empty_day_blocks() -> None:
    parser = RuleBasedTrainingTextParser()
    text = "7 Июля\n\nБег 5 км\n\n8 Июля\n\n9 Июля\n\nЗал"
    draft = parser.parse_week(text=text, start_date=date(2024, 7, 7))

    assert len(draft.workouts) == 2
    assert draft.workouts[0].planned_date == date(2024, 7, 7)
    assert draft.workouts[1].planned_date == date(2024, 7, 9)


def test_parse_week_uses_day_header_for_planned_date() -> None:
    parser = RuleBasedTrainingTextParser()
    text = "13 Июля\n\nБег\n\n14 Июля\n\nЗал"
    draft = parser.parse_week(text=text, start_date=date(2026, 7, 6))

    assert len(draft.workouts) == 2
    assert draft.workouts[0].planned_date == date(2026, 7, 13)
    assert draft.workouts[1].planned_date == date(2026, 7, 14)


def test_week_parser_ignores_duration_lines_as_day_headers() -> None:
    parser = RuleBasedTrainingTextParser()
    text = "7 Июля\n\nВелостанок\n\n60 мин\n\n9 Июля\n\nБег 5 км"
    draft = parser.parse_week(text=text, start_date=date(2024, 7, 7))

    assert len(draft.workouts) == 2
    assert draft.workouts[0].planned_date == date(2024, 7, 7)
    assert draft.workouts[1].planned_date == date(2024, 7, 9)


def test_day_fixture_parses_rounds_and_list_items() -> None:
    parser = RuleBasedTrainingTextParser()
    text = _read_fixture("day_2024-06-12.txt")
    draft = parser.parse_day(text=text, planned_date=date(2024, 6, 12))

    assert len(draft.workouts) == 1
    workout = draft.workouts[0]
    assert workout.workout_type is WorkoutType.GYM
    assert len(workout.cycles) >= 2
    assert any("раунда" in cycle.name.lower() for cycle in workout.cycles)
    assert any(any(ex.name.startswith("20 ") for ex in cycle.exercises) for cycle in workout.cycles)


def test_parse_day_ignores_structural_cycle_label() -> None:
    parser = RuleBasedTrainingTextParser()
    text = "Основная часть\n- Бег 5 км"
    draft = parser.parse_day(text=text, planned_date=date(2024, 7, 13))

    workout = draft.workouts[0]
    assert workout.cycles[0].name == "Основная часть"
    assert len(workout.cycles[0].exercises) == 1
    assert workout.cycles[0].exercises[0].name == "Бег 5 км"


def test_parse_day_ignores_reexported_structural_labels() -> None:
    parser = RuleBasedTrainingTextParser()
    text = """13 Июля

Основная часть
- 10/на сторону Отведения ноги
- 15 Скручиваний в Холлоу"""
    draft = parser.parse_day(text=text, planned_date=date(2026, 7, 13))

    workout = draft.workouts[0]
    exercise_names = [exercise.name for cycle in workout.cycles for exercise in cycle.exercises]
    assert "Основная часть" not in exercise_names
    assert len(exercise_names) == 2


def test_report_parser_extracts_garmin_url_and_load() -> None:
    parser = RuleBasedReportTextParser()
    text = _read_fixture("report_load_short.txt")
    draft = parser.parse_report_text(text=text)

    assert draft.garmin_url is not None
    assert "connect.garmin.com" in str(draft.garmin_url)
    assert draft.suggested_difficulty_rating == 6
