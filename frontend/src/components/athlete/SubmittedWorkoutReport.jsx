export function SubmittedWorkoutReport({ day }) {
  if (!day.showSubmittedReport) {
    return null;
  }

  return (
    <div className="submitted-workout-report">
      <p className="submitted-workout-report__label">Отчёт отправлен</p>
      <p className="submitted-workout-report__text">{day.reportText || "Отчёт без комментария."}</p>
      {day.reportRpe != null ? (
        <p className="submitted-workout-report__meta">
          RPE: <strong>{day.reportRpe}</strong>/10
        </p>
      ) : null}
    </div>
  );
}
