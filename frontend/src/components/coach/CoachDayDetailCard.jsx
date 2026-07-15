import { WorkoutTextView } from "../training/WorkoutTextView.jsx";

export function CoachDayDetailCard({ day }) {
  return (
    <div className="coach-day-detail">
      <WorkoutTextView
        dayFull={day.dayFull}
        title={day.type !== "Отдых" ? day.type : ""}
        dateLabel={day.shortDateLabel}
        status={day.status}
        workout={day.workout}
        emptyLabel={day.emptyLabel}
      />

      <hr className="coach-day-detail__divider" />

      <h3 className="coach-day-detail__report-label">Отчёт спортсмена</h3>

      {day.showSubmittedReport ? (
        <>
          <div className="coach-day-detail__report-card">
            <p>{day.reportText || "Отчёт без комментария."}</p>
          </div>
          <div className="coach-day-detail__report-meta">
            {day.reportRpe != null ? (
              <span>
                RPE: <strong>{day.reportRpe}</strong>/10
              </span>
            ) : null}
            {day.report?.garmin_url ? (
              <a href={day.report.garmin_url} target="_blank" rel="noopener noreferrer">
                Активность на часах
              </a>
            ) : null}
          </div>
        </>
      ) : (
        <p className="coach-day-detail__no-report">
          {day.hasPlan
            ? "Спортсмен ещё не отправил отчёт за этот день."
            : "Отчёт появится после назначения тренировки."}
        </p>
      )}
    </div>
  );
}
