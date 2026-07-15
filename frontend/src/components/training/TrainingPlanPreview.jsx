export function TrainingPlanPreview({ preview }) {
  if (!preview) {
    return null;
  }

  return (
    <div className="training-plan-preview">
      {preview.warnings && preview.warnings.length > 0 ? (
        <div className="warnings">
          <p className="meta">Предупреждения:</p>
          <ul>
            {preview.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {preview.workouts && preview.workouts.length > 0 ? (
        <div className="workout-list">
          {preview.workouts.map((workout) => (
            <div
              key={`${workout.planned_date}-${workout.workout_type}-${workout.title || ""}`}
              className="workout-card"
            >
              <p className="meta">
                {workout.planned_date} · {workout.workout_type}
                {workout.title ? ` · ${workout.title}` : ""}
              </p>
              {workout.cycles?.map((cycle) => (
                <div key={`${workout.planned_date}-${cycle.sort_order}`} className="cycle-preview">
                  <strong>{cycle.name}</strong>
                  <ul>
                    {cycle.exercises?.map((exercise) => (
                      <li key={`${cycle.sort_order}-${exercise.sort_order}`}>
                        {exercise.name}
                        {exercise.details ? ` — ${exercise.details}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : (
        <p className="meta">Структура плана пока пуста.</p>
      )}
    </div>
  );
}
