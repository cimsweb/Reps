from __future__ import annotations

from datetime import date, datetime

from application.dto.training import (
    PlannedWorkoutView,
    TrainingCalendarView,
    WorkoutCycleView,
    WorkoutExerciseView,
)
from application.services.training_plan_text_export import format_training_calendar_as_text
from infrastructure.parsing.rule_based_training_text_parser import RuleBasedTrainingTextParser


def test_format_training_calendar_as_text_renders_day_blocks_and_cycles() -> None:
    calendar = TrainingCalendarView(
        anchor_date=date(2024, 6, 8),
        period="week",
        workouts=(
            PlannedWorkoutView(
                id="w1",
                plan_id="p1",
                coach_id="c1",
                athlete_id="a1",
                planned_date=date(2024, 6, 8),
                workout_type="run",
                title="",
                created_at=datetime(2024, 6, 1),
                cycles=(
                    WorkoutCycleView(
                        id="cy1",
                        name="Суставная разминка",
                        sort_order=0,
                        exercises=(
                            WorkoutExerciseView(
                                id="e1",
                                name="Лёгкий бег",
                                details="20 мин",
                                sort_order=0,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    export = format_training_calendar_as_text(calendar)
    assert "8 Июня" in export.text
    assert "Суставная разминка" in export.text
    assert "- Лёгкий бег — 20 мин" in export.text


def test_format_training_calendar_omits_default_cycle_name() -> None:
    calendar = TrainingCalendarView(
        anchor_date=date(2026, 7, 13),
        period="week",
        workouts=(
            PlannedWorkoutView(
                id="w1",
                plan_id="p1",
                coach_id="c1",
                athlete_id="a1",
                planned_date=date(2026, 7, 13),
                workout_type="gym",
                title="",
                created_at=datetime(2026, 7, 1),
                cycles=(
                    WorkoutCycleView(
                        id="cy1",
                        name="Основная часть",
                        sort_order=0,
                        exercises=(
                            WorkoutExerciseView(
                                id="e1",
                                name="10 Отжиманий",
                                details="",
                                sort_order=0,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    export = format_training_calendar_as_text(calendar)
    assert "Основная часть" not in export.text
    assert "- 10 Отжиманий" in export.text


def test_export_round_trip_does_not_accumulate_structural_labels() -> None:
    parser = RuleBasedTrainingTextParser()
    text = """13 Июля

4 раунда:
- 10/на сторону Отведения ноги
- 15 Скручиваний в Холлоу"""
    draft = parser.parse_week(text=text, start_date=date(2026, 7, 13))
    calendar = TrainingCalendarView(
        anchor_date=date(2026, 7, 13),
        period="week",
        workouts=tuple(
            PlannedWorkoutView(
                id=f"w{index}",
                plan_id="p1",
                coach_id="c1",
                athlete_id="a1",
                planned_date=workout.planned_date,
                workout_type=workout.workout_type.value,
                title=workout.title or "",
                created_at=datetime(2026, 7, 1),
                cycles=tuple(
                    WorkoutCycleView(
                        id=f"cy{index}-{cycle_index}",
                        name=cycle.name,
                        sort_order=cycle.sort_order,
                        exercises=tuple(
                            WorkoutExerciseView(
                                id=f"e{index}-{cycle_index}-{exercise_index}",
                                name=exercise.name,
                                details=exercise.details,
                                sort_order=exercise.sort_order,
                            )
                            for exercise_index, exercise in enumerate(cycle.exercises)
                        ),
                    )
                    for cycle_index, cycle in enumerate(workout.cycles)
                ),
            )
            for index, workout in enumerate(draft.workouts)
        ),
    )

    export = format_training_calendar_as_text(calendar)
    reparsed = parser.parse_week(text=export.text, start_date=date(2026, 7, 13))
    exercise_names = [
        exercise.name
        for workout in reparsed.workouts
        for cycle in workout.cycles
        for exercise in cycle.exercises
    ]
    assert "Основная часть" not in exercise_names
    assert len(exercise_names) == 2
