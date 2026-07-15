# MVP2.2-004 — Search

## Goal

Отдавать клиенту состояние ИИ-сессий: история чата, текущий черновик, возможность продолжить прерванный диалог.

## Requirements

### Query use cases

- `GetPlanAgentSessionUseCase` — session + messages + latest draft + warnings от парсера
- `ListCoachActiveAgentSessionsUseCase` — незавершённые сессии по спортсменам (для badge «черновик»)
- `GetReportAgentSessionUseCase` — для спортсмена

### Read models

```json
{
  "session_id": "...",
  "status": "active",
  "messages": [
    { "role": "user", "content": "бег зал бег..." },
    { "role": "assistant", "content": "Какой объём...", "type": "question" },
    { "role": "assistant", "content": null, "type": "draft", "draft": { ... } }
  ],
  "can_confirm": true,
  "messages_remaining": 12
}
```

### API

- `GET /coach/training-plans/ai/sessions/{id}` — полная история (MVP2.2-001)
- `GET /coach/athletes/{id}/training-plans/ai/sessions/active` — активная сессия если есть
- `GET /athlete/planned-workouts/{id}/report/ai/sessions/active`

### Права доступа

- Coach — только свои plan sessions для своих athletes
- Athlete — только свои report sessions

### Не входит

- Поиск по всем сообщениям / full-text search
- Аналитика использования ИИ

## Acceptance Criteria

- [x] GET session возвращает ordered messages и draft
- [x] Active session lookup работает для coach и athlete
- [x] 403 для чужих сессий
- [x] HTTP-тесты
- [x] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [MVP2.2-003-indexing.md](MVP2.2-003-indexing.md) закрыт

## Декомпозиция

```
MVP2.2-004 — Search
 ├── GetPlanAgentSession, GetReportAgentSession
 ├── list active sessions
 └── HTTP GET endpoints
```
