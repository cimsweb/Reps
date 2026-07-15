from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from domain.entities.workout_type import WorkoutType
from domain.services.training_text_parsing import (
    ParsedCycleDraft,
    ParsedExerciseDraft,
    ParsedTrainingDraft,
    ParsedWorkoutDraft,
    TrainingTextParser,
)

_DAY_HEADER_RE = re.compile(
    r"^\s*(?P<day>\d{1,2})\s+(?P<month>[А-Яа-яЁё]+)\s*$",
    re.MULTILINE,
)


def count_day_headers(text: str) -> int:
    """Return how many day header lines (e.g. '7 Июля') appear in text."""
    return sum(1 for line in text.splitlines() if _is_valid_day_header_line(line))


def _is_valid_day_header_line(line: str) -> bool:
    match = _DAY_HEADER_RE.match(line.strip())
    if not match:
        return False
    day = int(match.group("day"))
    return 1 <= day <= 31


_MONTHS_RU = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def _resolve_header_planned_date(header_line: str, *, reference: date, fallback: date) -> date:
    match = _DAY_HEADER_RE.match(header_line.strip())
    if not match or not _is_valid_day_header_line(header_line):
        return fallback

    day = int(match.group("day"))
    month_key = match.group("month").lower().replace("ё", "е")
    month = _MONTHS_RU.get(month_key)
    if month is None:
        return fallback

    year = reference.year
    if reference.month == 1 and month == 12:
        year -= 1
    elif reference.month == 12 and month == 1:
        year += 1

    try:
        return date(year, month, day)
    except ValueError:
        return fallback


_LIST_ITEM_RE = re.compile(r"^\s*-\s+(?P<text>.+?)\s*$")
_ROUNDS_RE = re.compile(r"^\s*\d+\s*раунд", re.IGNORECASE)

_GYM_HINT_RE = re.compile(
    r"\b(подтягиван|отжиман|супермен|ягодичн|самолет|ножниц|холлоу|газонокосилк)\b",
    re.IGNORECASE,
)
_BIKE_HINT_RE = re.compile(r"\b(велостанок|вело)\b", re.IGNORECASE)
_STRUCTURAL_LABELS = frozenset({"основная часть", "план"})


def _is_structural_label(line: str) -> bool:
    return line.strip().lower() in _STRUCTURAL_LABELS


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Collapse 3+ newlines into 2 newlines to keep paragraph separation.
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def _infer_workout_type(day_text: str) -> WorkoutType:
    lower = day_text.lower()
    if _BIKE_HINT_RE.search(lower):
        return WorkoutType.BIKE
    if _GYM_HINT_RE.search(lower):
        return WorkoutType.GYM
    if "бег" in lower:
        return WorkoutType.RUN
    return WorkoutType.RUN


def _split_tsv_week(text: str) -> list[str] | None:
    # Typical copy-paste from Excel/Sheets gives one row with \t separators.
    if "\t" not in text:
        return None
    parts = [part.strip() for part in text.split("\t")]
    parts = [part for part in parts if part]
    if len(parts) < 2:
        return None
    return parts


def _split_blocks_by_day_header(text: str) -> list[str]:
    matches = [
        match
        for match in _DAY_HEADER_RE.finditer(text)
        if _is_valid_day_header_line(match.group(0))
    ]
    if not matches:
        return [text.strip()] if text.strip() else []

    blocks: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(text[start:end].strip())
    return [block for block in blocks if block]


@dataclass(frozen=True, slots=True)
class RuleBasedTrainingTextParser(TrainingTextParser):
    def parse_week(self, *, text: str, start_date: date) -> ParsedTrainingDraft:
        normalized = _normalize_text(text)
        warnings: list[str] = []

        tsv_days = _split_tsv_week(normalized)
        if tsv_days is not None:
            day_blocks = tsv_days
            if len(day_blocks) != 7:
                warnings.append(
                    "Ожидалось 7 дней в TSV, "
                    f"получено {len(day_blocks)} — распознано как список блоков"
                )
        else:
            day_blocks = _split_blocks_by_day_header(normalized)

        workouts: list[ParsedWorkoutDraft] = []
        for index, block in enumerate(day_blocks[:7]):
            first_line = block.split("\n", 1)[0].strip() if block else ""
            fallback_date = start_date + timedelta(days=index)
            planned_date = _resolve_header_planned_date(
                first_line,
                reference=start_date,
                fallback=fallback_date,
            )
            parsed_day = self.parse_day(text=block, planned_date=planned_date)
            warnings.extend(parsed_day.warnings)
            if not parsed_day.workouts:
                continue
            workout_draft = parsed_day.workouts[0]
            if not workout_draft.cycles:
                continue
            workouts.append(workout_draft)

        if len(day_blocks) == 1 and count_day_headers(normalized) >= 2:
            warnings.append(
                "Текст содержит несколько заголовков дней, но не был разбит — "
                "проверьте формат (каждый день с новой строки: '7 Июля')"
            )

        if len(day_blocks) > 7:
            warnings.append(
                f"Лишние дни в тексте недели: {len(day_blocks) - 7} блок(ов) проигнорированы"
            )

        # Ensure workouts sorted by planned_date
        workouts_sorted = tuple(sorted(workouts, key=lambda w: w.planned_date))
        return ParsedTrainingDraft(workouts=workouts_sorted, warnings=tuple(warnings))

    def parse_day(self, *, text: str, planned_date: date) -> ParsedTrainingDraft:
        normalized = _normalize_text(text)
        warnings: list[str] = []

        # Remove leading "DD Month" header if present.
        first_line = normalized.split("\n", 1)[0].strip() if normalized else ""
        if _is_valid_day_header_line(first_line):
            normalized = normalized[len(first_line) :].lstrip("\n").strip()

        workout_type = _infer_workout_type(text)

        exercises_buffer: list[ParsedExerciseDraft] = []
        cycles: list[ParsedCycleDraft] = []

        def flush_cycle(name: str, items: list[ParsedExerciseDraft]) -> None:
            if not items:
                return
            cycles.append(
                ParsedCycleDraft(
                    name=name,
                    sort_order=len(cycles),
                    exercises=tuple(items),
                )
            )

        current_cycle_name = "Основная часть"

        def start_new_cycle(name: str) -> None:
            nonlocal exercises_buffer, current_cycle_name
            flush_cycle(current_cycle_name, exercises_buffer)
            exercises_buffer = []
            current_cycle_name = name

        lines = [line.rstrip() for line in normalized.split("\n")]
        content_lines: list[str] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            content_lines.append(line)

            if _ROUNDS_RE.search(line):
                start_new_cycle(line)
                continue

            if line.lower() in {"суставная разминка", "растяжка", "сбу"}:
                start_new_cycle(line)
                continue

            if _is_structural_label(line):
                continue

            if _is_valid_day_header_line(line):
                continue

            list_match = _LIST_ITEM_RE.match(line)
            if list_match:
                item_text = list_match.group("text").strip()
                exercises_buffer.append(
                    ParsedExerciseDraft(
                        name=item_text,
                        details="",
                        sort_order=len(exercises_buffer),
                    )
                )
                continue

            # Free-form line → exercise.
            exercises_buffer.append(
                ParsedExerciseDraft(
                    name=line,
                    details="",
                    sort_order=len(exercises_buffer),
                )
            )

        flush_cycle(current_cycle_name, exercises_buffer)

        if not cycles:
            warnings.append("Не удалось распознать структуру дня: добавлен fallback-цикл")
            fallback_exercises = tuple(
                ParsedExerciseDraft(name=line, details="", sort_order=index)
                for index, line in enumerate(content_lines[:30])
            )
            if fallback_exercises:
                cycles.append(
                    ParsedCycleDraft(
                        name="План",
                        sort_order=0,
                        exercises=fallback_exercises,
                    )
                )

        workout = ParsedWorkoutDraft(
            planned_date=planned_date,
            workout_type=workout_type,
            title=None,
            cycles=tuple(cycles),
        )
        return ParsedTrainingDraft(workouts=(workout,), warnings=tuple(warnings))
