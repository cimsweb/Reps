import { formatDate, formatWorkoutType } from "../../utils/formatters.js";

export function TrainingWorkoutCard({ workout }) {
  return (
    <article className="workout-card">
      <header className="workout-card-header">
        <div>
          <strong>{workout.title || formatWorkoutType(workout.workout_type)}</strong>
          <p className="meta">
            {formatDate(workout.planned_date)} · {formatWorkoutType(workout.workout_type)}
          </p>
        </div>
      </header>
      {workout.cycles?.length ? (
        <div className="workout-card-body">
          {workout.cycles.map((cycle) => (
            <div key={cycle.id} className="cycle-block">
              <h3>{cycle.name}</h3>
              <ul className="exercise-list">
                {cycle.exercises.map((exercise) => (
                  <li key={exercise.id} className="exercise-row">
                    <strong>{exercise.name}</strong>
                    <span className="meta">{exercise.details}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <p className="meta">Упражнения не указаны.</p>
      )}
    </article>
  );
}
