import { addDaysToDateString, toDateInputValue } from "../../utils/formatters.js";

export function PeriodNavigator({ period, anchorDate, onPeriodChange, onAnchorDateChange }) {
  function shiftAnchor(days) {
    onAnchorDateChange(addDaysToDateString(anchorDate, days));
  }

  return (
    <div className="period-nav">
      <div className="stack-actions">
        <button
          type="button"
          className={period === "week" ? "" : "button-secondary"}
          onClick={() => onPeriodChange("week")}
        >
          Неделя
        </button>
        <button
          type="button"
          className={period === "month" ? "" : "button-secondary"}
          onClick={() => onPeriodChange("month")}
        >
          Месяц
        </button>
      </div>
      <div className="stack-actions period-nav-dates">
        <button type="button" className="button-secondary" onClick={() => shiftAnchor(-7)}>
          ←
        </button>
        <label className="period-nav-date">
          Опорная дата
          <input
            type="date"
            value={anchorDate}
            onChange={(event) => onAnchorDateChange(event.target.value)}
          />
        </label>
        <button type="button" className="button-secondary" onClick={() => shiftAnchor(7)}>
          →
        </button>
        <button
          type="button"
          className="button-secondary"
          onClick={() => onAnchorDateChange(toDateInputValue())}
        >
          Сегодня
        </button>
      </div>
    </div>
  );
}
