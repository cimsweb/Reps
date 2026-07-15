const STATUS_DOT_COLORS = {
  done: "var(--color-accent-green)",
  today: "var(--color-accent-blue)",
  soon: "var(--color-text-muted)",
  missed: "var(--color-error)",
  pending: "var(--color-accent-orange)",
};

export function WeekStrip({ days, selectedIndex, onSelectDay }) {
  return (
    <div className="week-strip" role="tablist" aria-label="Дни недели">
      {days.map((day, index) => {
        const isActive = index === selectedIndex;
        const dotColor = STATUS_DOT_COLORS[day.status] ?? STATUS_DOT_COLORS.soon;

        return (
          <button
            key={day.key}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={["week-strip__day", isActive ? "week-strip__day--active" : ""]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelectDay(index)}
          >
            <span className="week-strip__label">{day.label}</span>
            <span className="week-strip__date">{day.date.getDate()}</span>
            <span
              className="week-strip__dot"
              style={{ background: dotColor }}
              aria-hidden="true"
            />
          </button>
        );
      })}
    </div>
  );
}
