const STATUS_DOT_COLORS = {
  done: "var(--color-accent-green)",
  today: "var(--color-accent-blue)",
  soon: "var(--color-text-muted)",
  missed: "var(--color-error)",
  pending: "var(--color-accent-orange)",
};

export function CoachWeekGrid({ days, selectedIndex, onSelectDay }) {
  return (
    <div className="coach-week-grid" role="tablist" aria-label="Неделя спортсмена">
      {days.map((day, index) => {
        const isActive = index === selectedIndex;
        const dotColor = STATUS_DOT_COLORS[day.status] ?? STATUS_DOT_COLORS.soon;

        return (
          <button
            key={day.key}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={["coach-week-grid__day", isActive ? "coach-week-grid__day--active" : ""]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelectDay(index)}
          >
            <span className="coach-week-grid__label">{day.label}</span>
            <span className="coach-week-grid__type">{day.type}</span>
            <span
              className="coach-week-grid__dot"
              style={{ background: dotColor }}
              aria-hidden="true"
            />
            <span className="coach-week-grid__status">{day.statusLabel}</span>
          </button>
        );
      })}
    </div>
  );
}
