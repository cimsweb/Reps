# Conversations API

Base URL: `/api/v1`

Authentication and error format — see [auth.md](auth.md).

Human coach–athlete chat (distinct from AI agent sessions in [training-ai.md](training-ai.md)).

## Access rules

- Coach can message only **linked** athletes.
- Athlete can message only **linked** coaches.
- One conversation thread per coach–athlete pair.

## Message kinds

| Kind       | Description                          |
| ---------- | ------------------------------------ |
| `text`     | Regular message                      |
| `question` | Question to coach (UI orange accent) |

---

## GET /coach/conversations

List conversations for the authenticated coach. **Coach only.**

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "uuid",
            "coach_id": "uuid",
            "athlete_id": "uuid",
            "partner_id": "uuid",
            "partner_email": "athlete@example.com",
            "unread_count": 1,
            "last_message_content": "Как самочувствие?",
            "last_message_at": "2026-07-03T12:00:00Z",
            "updated_at": "2026-07-03T12:00:00Z"
        }
    ]
}
```

---

## GET /athlete/conversations

List conversations for the authenticated athlete. **Athlete only.**

Same response shape as coach list; `partner_id` / `partner_email` refer to the coach.

---

## GET /coach/conversations/{conversation_id}/messages

Paginated message history. **Coach only.**

Query: `offset` (default 0), `limit` (default 50, max 100).

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "uuid",
            "conversation_id": "uuid",
            "sender_id": "uuid",
            "kind": "text",
            "content": "Привет!",
            "sort_order": 0,
            "read_at": null,
            "created_at": "2026-07-03T12:00:00Z",
            "is_mine": true
        }
    ],
    "total": 1,
    "offset": 0,
    "limit": 50
}
```

---

## GET /athlete/conversations/{conversation_id}/messages

Same as coach endpoint. **Athlete only.**

---

## POST /coach/athletes/{athlete_id}/messages

Send a message to a linked athlete. Creates conversation on first message. **Coach only.**

**Request**

```json
{
    "content": "Как прошла тренировка?",
    "kind": "text"
}
```

**Response `201 Created`** — `ConversationMessage`

---

## POST /athlete/coaches/{coach_id}/messages

Send a message to a linked coach. **Athlete only.**

**Request**

```json
{
    "content": "Можно перенести тренировку на завтра?",
    "kind": "question"
}
```

**Response `201 Created`** — `ConversationMessage`

---

## POST /coach/conversations/{conversation_id}/read

Mark incoming messages as read. **Coach only.**

**Response `200 OK`**

```json
{
    "marked_count": 2
}
```

---

## POST /athlete/conversations/{conversation_id}/read

Mark incoming messages as read. **Athlete only.**

Same response as coach endpoint.

---

## Errors

| Status | Code               | When                                |
| ------ | ------------------ | ----------------------------------- |
| 400    | `validation_error` | Empty content or invalid kind       |
| 403    | `forbidden`        | Not linked or wrong role            |
| 404    | `not_found`        | Conversation does not exist / access |
