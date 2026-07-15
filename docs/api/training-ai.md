# Training AI API (MVP 2.2)

Base URL: `/api/v1`

Authentication and error format — see [auth.md](auth.md).

MVP 2.2-002 implements dialog use cases. Endpoints return **201/200** on success. When the AI provider is unavailable, responses use `503` with `"fallback": "manual"`.

## Session limits (domain rules)

| Rule                      | Value |
| ------------------------- | ----- |
| Max messages per session  | 20    |
| AI call timeout           | 30 s  |
| Session inactivity expiry | 24 h  |

## Environment

| Variable             | Description                            |
| -------------------- | -------------------------------------- |
| `AI_API_KEY`         | Provider API key (optional in 2.2-001) |
| `AI_BASE_URL`        | OpenAI-compatible base URL             |
| `AI_MODEL`           | Model name                             |
| `AI_TIMEOUT_SECONDS` | Request timeout (default 30)           |

---

## POST /coach/athletes/{athlete_id}/training-plans/ai/sessions

Start AI-assisted plan creation. **Coach only.**

**Request**

```json
{
    "start_date": "2026-06-08",
    "initial_brief": "бег зал бег отдых бег вело бег"
}
```

**Response `200 OK`** — `AgentSession` (when implemented in MVP 2.2-002)

**Response `501`** — dialog not implemented yet

---

## POST /coach/training-plans/ai/sessions/{session_id}/messages

Send coach message or answer a clarifying question. **Coach only.**

**Request**

```json
{
    "content": "120 минут в субботу"
}
```

**Response** — updated `AgentSession` with `latest_reply`:

- `type: "question"` — assistant asks for more input
- `type: "plan_draft"` — assistant suggests a plan draft

**Response `501`** — not implemented yet

---

## GET /coach/training-plans/ai/sessions/{session_id}

Get session state, message history, and latest draft. **Coach only.**

**Response `200 OK`** — `AgentSession` with ordered `messages` and `latest_reply` (including parser `warnings` on plan drafts).

---

## GET /coach/athletes/{athlete_id}/training-plans/ai/sessions/active

Return the active plan-creation session for a linked athlete, if any. **Coach only.**

**Response `200 OK`** — `AgentSession`

**Response `404`** — no active session

---

## POST /coach/training-plans/ai/sessions/{session_id}/confirm

Confirm draft and save as training plan. **Not automatic** — coach must call explicitly. **Coach only.**

**Request** (optional overrides)

```json
{
    "start_date": "2026-06-08",
    "scope": "week",
    "raw_text": "..."
}
```

**Response `501`** — not implemented yet

---

## POST /athlete/planned-workouts/{planned_workout_id}/report/ai/sessions

Start AI-assisted report session for a planned workout. **Athlete only.**

**Response `201 Created`** — `AgentSession`

---

## GET /athlete/report/ai/sessions/{session_id}

Get report session state and message history. **Athlete only.**

**Response `200 OK`** — `AgentSession`

---

## GET /athlete/planned-workouts/{planned_workout_id}/report/ai/sessions/active

Return the active report session for a planned workout, if any. **Athlete only.**

**Response `200 OK`** — `AgentSession`

**Response `404`** — no active session

---

## POST /athlete/report/ai/sessions/{session_id}/messages

Send athlete message in report dialog. **Athlete only.**

**Request**

```json
{
    "content": "нагрузка 5, тяжело на интервалах"
}
```

**Response** — `latest_reply` with `type: "question"` or `type: "report_draft"`

**Response `501`** — not implemented yet

---

## POST /athlete/report/ai/sessions/{session_id}/confirm

Confirm report draft and submit completion report. **Athlete only.**

**Request**

```json
{
    "difficulty_rating": 6,
    "mood_rating": 7,
    "comment": "Интервалы дались тяжело",
    "garmin_url": "https://connect.garmin.com/modern/activity/123",
    "raw_report_text": "нагрузка 5"
}
```

**Response `501`** — not implemented yet

---

## AgentSession response shape (target)

```json
{
    "session_id": "uuid",
    "kind": "plan_creation",
    "status": "active",
    "messages": [
        { "role": "user", "content": "...", "sort_order": 0 },
        { "role": "assistant", "content": "...", "sort_order": 1 }
    ],
    "messages_remaining": 18,
    "can_confirm": false,
    "latest_reply": {
        "type": "question",
        "text": "Какой объём длительного бега в субботу?"
    }
}
```

## Errors

| Status | Code              | When                         |
| ------ | ----------------- | ---------------------------- |
| 501    | `not_implemented` | MVP 2.2-002 not deployed     |
| 503    | `ai_unavailable`  | AI provider missing or down  |
| 403    | `forbidden`       | Wrong role or no coach link  |
| 404    | `not_found`       | Session or workout not found |
