import { StatusChip } from "../ui/StatusChip.jsx";
import { formatWorkoutDisplayText, toLines } from "../../utils/workoutText.js";

export function WorkoutTextView({
  dayFull,
  title,
  dateLabel,
  status,
  workout,
  bodyText,
  emptyLabel = "На этот день тренировка не назначена.",
}) {
  const displayText = bodyText ?? formatWorkoutDisplayText(workout);
  const lines = toLines(displayText);
  const hasPlan = Boolean(workout) || Boolean(displayText?.trim());
  const titleSuffix = title ? ` — ${title}` : "";

  return (
    <article className="workout-text-view">
      <header className="workout-text-view__header">
        <div>
          <h2 className="workout-text-view__title">
            {dayFull}
            {titleSuffix}
          </h2>
          {dateLabel ? <p className="workout-text-view__date">{dateLabel}</p> : null}
        </div>
        {status ? <StatusChip variant={status.variant} label={status.label} /> : null}
      </header>

      {hasPlan ? (
        <div className="workout-text-view__body">
          {lines.map((line, index) => {
            if (line.blank) {
              return <div key={`blank-${index}`} className="workout-text-view__spacer" aria-hidden="true" />;
            }
            if (line.bullet) {
              return (
                <div key={`bullet-${index}`} className="workout-text-view__line workout-text-view__line--bullet">
                  <span className="workout-text-view__bullet" aria-hidden="true">
                    •
                  </span>
                  <span>{line.text}</span>
                </div>
              );
            }
            return (
              <p key={`plain-${index}`} className="workout-text-view__line">
                {line.text}
              </p>
            );
          })}
        </div>
      ) : (
        <p className="workout-text-view__empty">{emptyLabel}</p>
      )}
    </article>
  );
}
