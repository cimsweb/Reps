# Training database schema (MVP 2)

## Tables

| Table                        | Purpose                                   |
| ---------------------------- | ----------------------------------------- |
| `training_plans`             | Coach plan container (day or week scope)  |
| `planned_workouts`           | Single workout on a calendar date         |
| `workout_cycles`             | Named cycle inside a workout              |
| `workout_exercises`          | Exercise or interval in a cycle           |
| `workout_completion_reports` | Athlete report after completing a workout |

## Foreign keys and cascades

All training tables reference `users.id` or parent training rows with `ON DELETE CASCADE`:

- deleting a user removes their plans, workouts, and reports
- deleting a plan removes its workouts, cycles, and exercises
- deleting a workout removes its cycles, exercises, and report

## Invariants

- Plan belongs to one `coach_id` and one `athlete_id` (linked pair from MVP 1)
- One `workout_completion_reports` row per `planned_workout_id` (UNIQUE)
- `difficulty_rating` and `mood_rating` are integers 0–10 (enforced in domain)
- `WorkoutFeedback` (MVP 1) and `WorkoutCompletionReport` (MVP 2) are separate entities

## MVP 2.1 extensions (migration 005)

- `training_plans.raw_text` — optional source text (coach free-form input)
- `workout_completion_reports.garmin_url` — optional Garmin Connect URL
- `workout_completion_reports.raw_report_text` — optional source text (athlete free-form input)

## ENUM types

| Type           | Values               |
| -------------- | -------------------- |
| `plan_scope`   | `day`, `week`        |
| `workout_type` | `run`, `bike`, `gym` |

## Indexes (migration 004)

| Index                                                 | Purpose                     |
| ----------------------------------------------------- | --------------------------- |
| `training_plans (coach_id)`, `(athlete_id)`           | Plan lookups by user        |
| `planned_workouts (athlete_id, planned_date)`         | Calendar week/month queries |
| `planned_workouts (coach_id, planned_date)`           | Coach calendar queries      |
| `workout_cycles (planned_workout_id)`                 | Load workout structure      |
| `workout_exercises (cycle_id)`                        | Load cycle exercises        |
| `workout_completion_reports (athlete_id, created_at)` | Report period queries       |
| `UNIQUE (planned_workout_id)` on reports              | One report per workout      |

## Access rules

- Athletes access only rows where `athlete_id` equals their user id
- Coaches access athlete rows only when `coach_athlete_links` exists (MVP 1)
- Enforced by `TrainingAccessGuard` in application layer (MVP2-003)
- Ownership helpers in `domain/services/training_ownership.py` validate coach-athlete pair consistency
