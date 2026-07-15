import { formatPaceSecondsPerKm, formatWorkoutType, toDateInputValue } from "./formatters.js";
import { startOfWeek } from "./weekStrip.js";

const WEEKDAY_FULL = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
  "Воскресенье",
];

function normalizeDate(date) {
  const normalized = new Date(date);
  normalized.setHours(0, 0, 0, 0);
  return normalized;
}

export function isSameCalendarDay(left, right) {
  const a = normalizeDate(left);
  const b = normalizeDate(right);
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function cycleMatches(cycleName, keyword) {
  return cycleName.toLowerCase().includes(keyword);
}

function formatCycleText(cycle) {
  if (!cycle?.exercises?.length) {
    return "—";
  }
  return cycle.exercises
    .map((exercise) => {
      const details = exercise.details?.trim();
      return details ? `${exercise.name}: ${details}` : exercise.name;
    })
    .join("; ");
}

function findCycleText(cycles, keyword) {
  const cycle = cycles.find((item) => cycleMatches(item.name, keyword));
  return cycle ? formatCycleText(cycle) : "—";
}

function collectExerciseText(cycles) {
  return cycles
    .flatMap((cycle) => cycle.exercises ?? [])
    .map((exercise) => `${exercise.name} ${exercise.details ?? ""}`)
    .join(" ");
}

function extractPaceLabel(cycles) {
  const text = collectExerciseText(cycles);
  const paceMatch = text.match(/\d{1,2}:\d{2}\s*\/?\s*км/i);
  if (paceMatch) {
    return paceMatch[0].replace(/\s+/g, "");
  }
  const tempoMatch = text.match(/темп[:\s]+(\d{1,2}:\d{2})/i);
  if (tempoMatch) {
    return `${tempoMatch[1]}/км`;
  }
  return "—";
}

function extractHeartRateZone(cycles) {
  const text = collectExerciseText(cycles);
  const zoneMatch = text.match(/(?:zone|зон[аы])\s*([\d\-–]+)/i);
  if (zoneMatch) {
    return `Zone ${zoneMatch[1]}`;
  }
  return "—";
}

export function resolveWorkoutForDate(workouts, date) {
  const dateKey = toDateInputValue(date);
  return (
    workouts.find((workout) => normalizePlannedDate(workout.planned_date) === dateKey) ?? null
  );
}

function normalizePlannedDate(value) {
  if (!value) {
    return "";
  }
  return String(value).slice(0, 10);
}

export function buildReportIndex(reports) {
  const byWorkoutId = new Map();
  for (const report of reports) {
    byWorkoutId.set(report.planned_workout_id, report);
  }
  return byWorkoutId;
}

export function resolveDayStatus(workout, report, date, today = new Date()) {
  const day = normalizeDate(date);
  const now = normalizeDate(today);

  if (!workout) {
    return { variant: "soon", label: "Отдых", stripStatus: "soon" };
  }

  if (report) {
    return { variant: "done", label: "Выполнено", stripStatus: "done" };
  }

  if (isSameCalendarDay(day, now)) {
    return { variant: "today", label: "Сегодня", stripStatus: "today" };
  }

  if (day < now) {
    return { variant: "missed", label: "Пропущено", stripStatus: "missed" };
  }

  return { variant: "soon", label: "Скоро", stripStatus: "soon" };
}

export function buildDayViewModel(workout, report, date, today = new Date()) {
  const status = resolveDayStatus(workout, report, date, today);
  const cycles = workout?.cycles ?? [];
  const weekdayIndex = (normalizeDate(date).getDay() + 6) % 7;

  return {
    date,
    dayFull: WEEKDAY_FULL[weekdayIndex],
    dateLabel: normalizeDate(date).toLocaleDateString("ru-RU", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }),
    shortDateLabel: normalizeDate(date).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
    }),
    hasPlan: Boolean(workout),
    workout,
    report,
    status,
    type: workout?.title || formatWorkoutType(workout?.workout_type) || "Отдых",
    warmup: findCycleText(cycles, "размин"),
    main: findCycleText(cycles, "основ") || formatCycleText(cycles[0]),
    cooldown: findCycleText(cycles, "замин"),
    pace: extractPaceLabel(cycles),
    hrZone: extractHeartRateZone(cycles),
    canReport: Boolean(workout && !report),
    showSubmittedReport: Boolean(workout && report),
    reportText: report?.comment || report?.raw_report_text || "",
    reportRpe: report?.difficulty_rating ?? null,
    emptyLabel: "На этот день тренировка не назначена.",
  };
}

export function calculateWeekCompliance(workouts, reports, today = new Date(), anchorDate = today) {
  const weekStart = normalizeDate(startOfWeek(anchorDate));
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  weekEnd.setHours(23, 59, 59, 999);

  const now = normalizeDate(today);
  const reportIndex = buildReportIndex(reports);
  const planned = workouts.filter((workout) => {
    const date = normalizeDate(`${workout.planned_date}T00:00:00`);
    return date >= weekStart && date <= weekEnd && date <= now;
  });

  if (planned.length === 0) {
    return null;
  }

  const completed = planned.filter((workout) => reportIndex.has(workout.id)).length;
  return Math.round((completed / planned.length) * 100);
}

export function formatReportPace(report) {
  if (!report?.pace_seconds_per_km) {
    return null;
  }
  return formatPaceSecondsPerKm(report.pace_seconds_per_km);
}
