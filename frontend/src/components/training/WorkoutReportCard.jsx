import { formatDateTime } from "../../utils/formatters.js";

export function WorkoutReportCard({ report }) {
  return (
    <article className="workout-card report-card">
      <p className="meta">{formatDateTime(report.created_at)}</p>
      <dl className="report-ratings">
        <div>
          <dt>Трудность</dt>
          <dd>{report.difficulty_rating}/10</dd>
        </div>
        <div>
          <dt>Эмоции</dt>
          <dd>{report.mood_rating}/10</dd>
        </div>
      </dl>
      {report.comment ? <p>{report.comment}</p> : null}
    </article>
  );
}
