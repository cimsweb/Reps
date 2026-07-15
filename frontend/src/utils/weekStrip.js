const WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function startOfWeek(date) {
  const normalized = new Date(date);
  normalized.setHours(0, 0, 0, 0);
  const weekday = normalized.getDay();
  const mondayOffset = weekday === 0 ? -6 : 1 - weekday;
  normalized.setDate(normalized.getDate() + mondayOffset);
  return normalized;
}

function isSameDay(left, right) {
  return (
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()
  );
}

export function isSameWeek(leftDate, rightDate) {
  const leftStart = startOfWeek(leftDate).getTime();
  const rightStart = startOfWeek(rightDate).getTime();
  return leftStart === rightStart;
}

export function formatWeekRangeLabel(anchorDate) {
  const start = startOfWeek(anchorDate);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  const startLabel = start.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: start.getMonth() === end.getMonth() ? undefined : "long",
  });
  const endLabel = end.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
  });

  return `${startLabel} – ${endLabel}`;
}

/**
 * Build seven days for the week strip (Monday-based).
 */
export function buildWeekStripDays(anchorDate = new Date()) {
  const weekStart = startOfWeek(anchorDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return WEEKDAY_LABELS.map((label, index) => {
    const date = new Date(weekStart);
    date.setDate(weekStart.getDate() + index);

    let status = "soon";
    if (isSameDay(date, today)) {
      status = "today";
    }

    return {
      key: date.toISOString(),
      label,
      date,
      status,
    };
  });
}

export function findWeekDayIndex(days, targetDate) {
  return days.findIndex((day) => isSameDay(day.date, targetDate));
}
