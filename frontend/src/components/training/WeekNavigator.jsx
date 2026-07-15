import { addDaysToDateString } from "../../utils/formatters.js";
import { formatWeekRangeLabel } from "../../utils/weekStrip.js";

export function WeekNavigator({
  anchorDate,
  onAnchorDateChange,
  onDayIndexChange,
  compact = false,
}) {
  const weekRangeLabel = formatWeekRangeLabel(new Date(`${anchorDate}T00:00:00`));

  function shiftWeek(direction) {
    const nextAnchor = addDaysToDateString(anchorDate, direction * 7);
    onAnchorDateChange(nextAnchor);
    onDayIndexChange?.(nextAnchor);
  }

  function handleDatePick(event) {
    const pickedDate = event.target.value;
    if (!pickedDate) {
      return;
    }
    onAnchorDateChange(pickedDate);
    onDayIndexChange?.(pickedDate);
  }

  return (
    <div className={["week-navigator", compact ? "week-navigator--compact" : ""].filter(Boolean).join(" ")}>
      <div className="week-navigator__controls">
        <button
          type="button"
          className="week-navigator__arrow"
          aria-label="Предыдущая неделя"
          onClick={() => shiftWeek(-1)}
        >
          ‹
        </button>
        <span className="week-navigator__label">{weekRangeLabel}</span>
        <button
          type="button"
          className="week-navigator__arrow"
          aria-label="Следующая неделя"
          onClick={() => shiftWeek(1)}
        >
          ›
        </button>
      </div>
      <input
        type="date"
        className="week-navigator__date"
        value={anchorDate}
        onChange={handleDatePick}
        aria-label="Выбрать дату"
      />
    </div>
  );
}
