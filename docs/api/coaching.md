# Coaching API (MVP 1)

Base URL: `/api/v1`

Authentication and error format — see [auth.md](auth.md).

All timestamps are ISO-8601 UTC.

## Roles

| Role      | Coaching capabilities                                         |
| --------- | ------------------------------------------------------------- |
| `coach`   | Send invitations, list athletes, view linked athlete data     |
| `athlete` | Accept/decline invitations, manage profile, records, feedback |

Coach access to athlete data is limited to athletes linked via accepted invitation.

Database indexes and integrity rules: [coaching-schema.md](../db/coaching-schema.md).

---

## POST /coach/invitations

Send an invitation to an athlete email. **Coach only.**

**Request**

```json
{
    "email": "athlete@example.com"
}
```

**Response `201 Created`**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "coach_id": "660e8400-e29b-41d4-a716-446655440001",
    "athlete_email": "athlete@example.com",
    "status": "pending",
    "created_at": "2026-06-29T12:00:00Z",
    "responded_at": null
}
```

**Errors**

| Status | Code               | When                                      |
| ------ | ------------------ | ----------------------------------------- |
| 400    | `validation_error` | Invalid email                             |
| 403    | `forbidden`        | Not a coach                               |
| 409    | `conflict`         | Pending invitation or link already exists |

---

## GET /coach/invitations

List invitations created by the authenticated coach. **Coach only.**

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "coach_id": "660e8400-e29b-41d4-a716-446655440001",
            "athlete_email": "athlete@example.com",
            "status": "pending",
            "created_at": "2026-06-29T12:00:00Z",
            "responded_at": null
        }
    ]
}
```

---

## GET /athlete/invitations

List pending invitations for the authenticated athlete email. **Athlete only.**

**Response `200 OK`** — same item shape as above.

---

## POST /athlete/invitations/{invitation_id}/accept

Accept a pending invitation. Creates `CoachAthleteLink`. **Athlete only.**

**Response `200 OK`**

```json
{
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "coach_id": "660e8400-e29b-41d4-a716-446655440001",
    "athlete_id": "880e8400-e29b-41d4-a716-446655440003",
    "created_at": "2026-06-29T12:05:00Z"
}
```

---

## POST /athlete/invitations/{invitation_id}/decline

Decline a pending invitation. **Athlete only.**

**Response `204 No Content`**

---

## GET /coach/athletes

List athletes linked to the coach. **Coach only.**

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "coach_id": "660e8400-e29b-41d4-a716-446655440001",
            "athlete_id": "880e8400-e29b-41d4-a716-446655440003",
            "created_at": "2026-06-29T12:05:00Z"
        }
    ]
}
```

---

## GET /athlete/coaches

List coaches linked to the athlete. **Athlete only.**

**Response `200 OK`** — same item shape as `/coach/athletes`.

---

## GET /athlete/profile

Get own athlete profile. **Athlete only.**

**Response `200 OK`**

```json
{
    "athlete_id": "880e8400-e29b-41d4-a716-446655440003",
    "height_cm": 180,
    "weight_kg": 75,
    "age": 28,
    "gender": "male",
    "updated_at": "2026-06-29T12:10:00Z"
}
```

---

## PUT /athlete/profile

Create or update own profile. **Athlete only.**

**Request** — `height_cm`, `weight_kg`, `age`, `gender`.

**Response `200 OK`** — profile object.

---

## GET /coach/athletes/{athlete_id}/profile

View linked athlete profile. **Coach only.**

---

## GET /athlete/records

List own personal records. **Athlete only.**

Query: `offset` (default 0), `limit` (default 20, max 100).

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "990e8400-e29b-41d4-a716-446655440004",
            "athlete_id": "880e8400-e29b-41d4-a716-446655440003",
            "record_type": "distance",
            "name": "5K",
            "value": "19:45",
            "unit": "time",
            "achieved_at": "2026-06-01T08:00:00Z",
            "created_at": "2026-06-29T12:15:00Z"
        }
    ],
    "total": 1
}
```

---

## POST /athlete/records

Create a personal record. **Athlete only.**

---

## PUT /athlete/records/{record_id}

Update own record. **Athlete only.**

---

## DELETE /athlete/records/{record_id}

Delete own record. **Athlete only.**

---

## GET /coach/athletes/{athlete_id}/records

List records for a linked athlete. **Coach only.**

Query: `offset` (default 0), `limit` (default 20, max 100).

**Response `200 OK`** — same shape as `/athlete/records`.

## GET /athlete/feedback

List own workout feedback. **Athlete only.**

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "aa0e8400-e29b-41d4-a716-446655440005",
            "athlete_id": "880e8400-e29b-41d4-a716-446655440003",
            "text": "Legs felt heavy on intervals.",
            "garmin_url": "https://connect.garmin.com/modern/activity/12345",
            "created_at": "2026-06-29T18:00:00Z"
        }
    ],
    "total": 1
}
```

---

## POST /athlete/feedback

Submit workout feedback. **Athlete only.**

**Request**

```json
{
    "text": "Legs felt heavy on intervals.",
    "garmin_url": "https://connect.garmin.com/modern/activity/12345"
}
```

| Field        | Rules                                 |
| ------------ | ------------------------------------- |
| `text`       | Required, non-empty                   |
| `garmin_url` | Optional; HTTPS URL on `*.garmin.com` |

---

## GET /coach/athletes/{athlete_id}/feedback

List feedback for a linked athlete. **Coach only.**

Query: `offset` (default 0), `limit` (default 20, max 100).

**Response `200 OK`** — same shape as `/athlete/feedback`.

## Logging events

| Event                          | When                  |
| ------------------------------ | --------------------- |
| `invitation_created`           | Coach sent invitation |
| `invitation_accepted`          | Athlete accepted      |
| `invitation_declined`          | Athlete declined      |
| `athlete_profile_saved`        | Profile saved         |
| `personal_record_saved`        | Record saved          |
| `personal_record_deleted`      | Record deleted        |
| `workout_feedback_submitted`   | Feedback saved        |
| `coaching_validation_error`    | Validation failed     |
| `coaching_authorization_error` | Access denied         |
