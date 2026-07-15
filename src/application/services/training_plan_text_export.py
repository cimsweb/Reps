from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from application.dto.training import PlannedWorkoutView, TrainingCalendarView, WorkoutCycleView


@dataclass(frozen=True, slots=True)
class TrainingPlanTextExport:
    """Readable text representation of a training plan for a period."""

    text: str


_DEFAULT_CYCLE_NAMES = frozenset({"Основная часть", "План"})

_MONTHS_RU = {
    1: "Января",
    2: "Февраля",
    3: "Марта",
    4: "Апреля",
    5: "Мая",
    6: "Июня",
    7: "Июля",
    8: "Августа",
    9: "Сентября",
    10: "Октября",
    11: "Ноября",
    12: "Декабря",
}


def _format_day_header(value: date) -> str:
    month = _MONTHS_RU.get(value.month, value.strftime("%B"))
    return f"{value.day} {month}"


def _format_cycle(cycle: WorkoutCycleView) -> str:
    lines: list[str] = []
    if cycle.name and cycle.name not in _DEFAULT_CYCLE_NAMES:
        lines.append(cycle.name)
    for exercise in cycle.exercises:
        details = exercise.details.strip()
        if details:
            lines.append(f"- {exercise.name} — {details}")
        else:
            lines.append(f"- {exercise.name}")
    return "\n".join(lines)


def format_training_calendar_as_text(calendar: TrainingCalendarView) -> TrainingPlanTextExport:
    """Render a calendar view into coach-friendly text blocks per day."""

    if not calendar.workouts:
        return TrainingPlanTextExport(text="")

    blocks: list[str] = []
    workouts_sorted = sorted(calendar.workouts, key=lambda w: w.planned_date)
    for workout in workouts_sorted:
        blocks.append(_format_workout_block(workout))

    return TrainingPlanTextExport(text="\n\n".join(blocks).strip() + "\n")


def _format_workout_block(workout: PlannedWorkoutView) -> str:
    lines: list[str] = [_format_day_header(workout.planned_date), ""]

    if workout.cycles:
        for index, cycle in enumerate(workout.cycles):
            if index > 0:
                lines.append("")
            lines.append(_format_cycle(cycle))
    else:
        lines.append(workout.title or workout.workout_type)

    return "\n".join(lines).strip()
