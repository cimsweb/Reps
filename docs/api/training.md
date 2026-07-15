# Training API (MVP 2)

Base URL: `/api/v1`

Authentication and error format — see [auth.md](auth.md).

Dates are ISO-8601 (`YYYY-MM-DD`). Timestamps are ISO-8601 UTC.

## Roles

| Role      | Training capabilities                                             |
| --------- | ----------------------------------------------------------------- |
| `coach`   | Create and edit plans for linked athletes; view plans and reports |
| `athlete` | View own plan; submit completion reports                          |

Coach access is limited to athletes linked via accepted invitation (MVP 1).

Database schema: [training-schema.md](../db/training-schema.md).

---

## POST /coach/athletes/{athlete_id}/training-plans/day

Create a training plan for a single day. **Coach only.**

**Request**

```json
{
    "start_date": "2026-06-30",
    "workouts": [
        {
            "planned_date": "2026-06-30",
            "workout_type": "run",
            "title": "Интервалы",
            "cycles": [
                {
                    "name": "Разминка",
                    "sort_order": 0,
                    "exercises": [
                        {
                            "name": "Лёгкий бег",
                            "details": "15 мин",
                            "sort_order": 0
                        }
                    ]
                }
            ]
        }
    ]
}
```

| Field          | Rules                          |
| -------------- | ------------------------------ |
| `workout_type` | `run`, `bike`, `gym`           |
| `cycles`       | One or more cycles per workout |
| `exercises`    | Ordered list inside each cycle |

**Response `201 Created`** — `TrainingPlan` with nested workouts, cycles, exercises.

**Errors**

| Status | Code               | When                              |
| ------ | ------------------ | --------------------------------- |
| 400    | `validation_error` | Invalid payload                   |
| 403    | `forbidden`        | Not a coach or athlete not linked |
| 409    | `conflict`         | Workout already exists for date   |

---

## POST /coach/athletes/{athlete_id}/training-plans/week

Create a training plan for seven days starting at `start_date`. **Coach only.**

**Request** — same shape as day plan; `workouts` may span up to 7 dates from `start_date`.

**Response `201 Created`** — `TrainingPlan` object.

---

## PUT /coach/planned-workouts/{workout_id}

Update a planned workout (type, title, cycles, exercises). **Coach only.**

**Response `200 OK`** — updated `PlannedWorkout`.

---

## DELETE /coach/planned-workouts/{workout_id}

Delete a planned workout and nested cycles/exercises. **Coach only.**

**Response `204 No Content`**

---

## POST /athlete/planned-workouts/{workout_id}/report

Submit a completion report for a planned workout. **Athlete only.**

**Request**

```json
{
    "difficulty_rating": 7,
    "mood_rating": 8,
    "comment": "Интервалы дались тяжело, но настроение хорошее",
    "garmin_url": "https://connect.garmin.com/modern/activity/23170671126",
    "raw_report_text": "Просмотрите мое занятие «бег» в Garmin Connect. #beatyesterday https://connect.garmin.com/modern/activity/23170671126"
}
```

| Field               | Rules                                   |
| ------------------- | --------------------------------------- |
| `difficulty_rating` | Required, integer 0–10 (10 = hardest)   |
| `mood_rating`       | Required, integer 0–10 (10 = best mood) |
| `comment`           | Optional text                           |
| `garmin_url`        | Optional Garmin Connect HTTPS URL       |
| `raw_report_text`   | Optional free-form source text          |

**Response `201 Created`**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "planned_workout_id": "660e8400-e29b-41d4-a716-446655440001",
    "athlete_id": "770e8400-e29b-41d4-a716-446655440002",
    "difficulty_rating": 7,
    "mood_rating": 8,
    "comment": "Интервалы дались тяжело, но настроение хорошее",
    "garmin_url": "https://connect.garmin.com/modern/activity/23170671126",
    "raw_report_text": "Просмотрите мое занятие «бег» в Garmin Connect. #beatyesterday https://connect.garmin.com/modern/activity/23170671126",
    "created_at": "2026-06-30T18:00:00Z"
}
```

---

## POST /coach/athletes/{athlete_id}/training-plans/parse (MVP 2.1)

Parse training plan free text and return a preview without saving. **Coach only.**

> In MVP2.1-001 this endpoint returns `501 not_implemented` until parsing is implemented.

**Request**

```json
{
    "scope": "week",
    "start_date": "2026-06-08",
    "text": "8 Июня\\n\\nСуставная разминка\\n..."
}
```

---

## POST /coach/athletes/{athlete_id}/training-plans/from-text (MVP 2.1)

Create a training plan from free text. **Coach only.**

---

## PATCH /coach/training-plans/{plan_id}/raw-text (MVP 2.1)

Update training plan raw text and re-parse **future** workouts. **Coach only.**

Past workouts and their reports are preserved.

**Request**

```json
{
    "raw_text": "8 Июня\\n\\nСуставная разминка\\n..."
}
```

**Response `200 OK`**

```json
{
    "plan": { "id": "...", "raw_text": "..." },
    "replaced_workouts_count": 3
}
```

**Errors**

| Status | Code               | When                     |
| ------ | ------------------ | ------------------------ |
| 400    | `validation_error` | Rating out of range      |
| 403    | `forbidden`        | Not the assigned athlete |
| 404    | `not_found`        | Workout not found        |
| 409    | `conflict`         | Report already exists    |

---

## GET /coach/athletes/{athlete_id}/training-plan

View linked athlete training plan. **Coach only.**

Query:

| Param         | Values          | Default |
| ------------- | --------------- | ------- |
| `period`      | `week`, `month` | `week`  |
| `anchor_date` | ISO date        | today   |

`week` — 7 days forward from `anchor_date` (inclusive).  
`month` — calendar month containing `anchor_date`.

**Response `200 OK`**

```json
{
    "anchor_date": "2026-06-30",
    "period": "week",
    "workouts": []
}
```

---

## GET /coach/athletes/{athlete_id}/training-plan/text (MVP 2.1)

View linked athlete training plan as readable text. **Coach only.**

Query params: same as `/coach/athletes/{athlete_id}/training-plan`.

**Response `200 OK`**

```json
{
    "anchor_date": "2026-06-30",
    "period": "week",
    "text": "30 Июня\\n\\nРазминка\\n- ...\\n"
}
```

---

## GET /athlete/training-plan

View own training plan. **Athlete only.**

Query: same as coach endpoint.

---

## GET /athlete/training-plan/text (MVP 2.1)

View own training plan as readable text. **Athlete only.**

Query params: same as `/athlete/training-plan`.

---

## GET /coach/athletes/{athlete_id}/workout-reports

List completion reports for a linked athlete. **Coach only.**

Query:

| Param         | Values          | Default |
| ------------- | --------------- | ------- |
| `period`      | `week`, `month` | `week`  |
| `anchor_date` | ISO date        | today   |

`week` = 7 days ending at `anchor_date`; `month` = 30 days.

**Response `200 OK`**

```json
{
    "anchor_date": "2026-06-30",
    "period": "week",
    "reports": []
}
```

---

## GET /athlete/workout-reports

List own completion reports. **Athlete only.**

Query and response — same as coach endpoint.

---

## Logging events

| Event                                 | When                     |
| ------------------------------------- | ------------------------ |
| `training_plan_created`               | Coach created a plan     |
| `training_plan_updated`               | Coach updated a workout  |
| `workout_completion_report_submitted` | Athlete submitted report |
| `training_validation_error`           | Validation failed        |
| `training_authorization_error`        | Access denied            |
