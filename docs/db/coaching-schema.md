# Coaching database schema (MVP 1)

## Tables

| Table                 | Purpose                                    |
| --------------------- | ------------------------------------------ |
| `invitations`         | Coach invitations by athlete email         |
| `coach_athlete_links` | Accepted coach ↔ athlete relationships     |
| `athlete_profiles`    | Athlete physical profile (1:1 with user)   |
| `personal_records`    | Distance and exercise personal bests       |
| `workout_feedback`    | Post-workout notes and optional Garmin URL |

## Foreign keys and cascades

All coaching tables reference `users.id` with `ON DELETE CASCADE`:

- deleting a user removes their invitations, links, profile, records, and feedback
- athlete profile uses `athlete_id` as primary key

## Invariants

- `CoachAthleteLink` is created only when an invitation is **accepted**
- declined invitations never create links
- one athlete may have multiple coaches (`UNIQUE (coach_id, athlete_id)`)
- profile, records, and feedback always belong to a single `athlete_id`

## Indexes

### Migration 002

| Table                 | Index                           | Purpose                               |
| --------------------- | ------------------------------- | ------------------------------------- |
| `invitations`         | `coach_id`                      | Coach invitation lists                |
| `invitations`         | `athlete_email`                 | Pending invitations for athlete email |
| `invitations`         | `status`                        | Status filtering                      |
| `coach_athlete_links` | `coach_id`, `athlete_id`        | Link lookups                          |
| `coach_athlete_links` | `UNIQUE (coach_id, athlete_id)` | Prevent duplicate links               |
| `personal_records`    | `athlete_id`                    | Athlete record lists                  |
| `workout_feedback`    | `athlete_id`                    | Athlete feedback history              |

### Migration 003 (composite)

| Index                                        | Purpose                                               |
| -------------------------------------------- | ----------------------------------------------------- |
| `invitations (coach_id, status)`             | Coach invitations by status without extra filter step |
| `personal_records (athlete_id, record_type)` | Group records by distance / exercise                  |
| `workout_feedback (athlete_id, created_at)`  | Sorted feedback history and pagination                |

## Access rules

- Athletes access only rows where `athlete_id` equals their user id
- Coaches access athlete rows only when a `coach_athlete_links` row exists
- enforced by `CoachingAccessGuard` in application layer (MVP1-003)
